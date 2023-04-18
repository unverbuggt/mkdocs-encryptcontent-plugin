
import os
import re
import base64
import hashlib
import logging
import json
import math
from pathlib import Path
from os.path import exists
from jinja2 import Template
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from bs4 import BeautifulSoup
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from urllib.parse import urlsplit
from urllib.request import urlopen

try:
    from mkdocs.utils import string_types
except ImportError:
    string_types = str

JS_LIBRARIES = [
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/core.js','b55ae8027253d4d54c4f1ef3b6254646'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/enc-base64.js','f551ce1340a86e5edbfef4a6aefa798f'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/cipher-core.js','dfddc0e33faf7a794e0c3c140544490e'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/sha256.js','561d24c90633fb34c13537a330d12786'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/hmac.js','ee162ca0ed3b55dd9b2fe74a3464bb74'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/pbkdf2.js','b9511c07dfe692c2fd7a9ecd3f27650e'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/aes.js','da81b91b1b57c279c29b3469649d9b86'],
]

PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))

SETTINGS = {
    'title_prefix': '[Protected] ',
    'summary': 'This content is protected with AES encryption. ',
    'placeholder': 'Use CTRL+ENTER to provide global password',
    'password_button_text': 'Decrypt',
    'decryption_failure_message': 'Invalid password.',
    'encryption_info_message': 'Contact your administrator for access to this page.'
}

logger = logging.getLogger("mkdocs.plugins.encryptcontent")
base_path = os.path.dirname(os.path.abspath(__file__))


class encryptContentPlugin(BasePlugin):
    """ Plugin that encrypt markdown content with AES and inject decrypt form. """

    config_scheme = (
        # default customization
        ('title_prefix', config_options.Type(string_types, default=str(SETTINGS['title_prefix']))),
        ('summary', config_options.Type(string_types, default=str(SETTINGS['summary']))),
        ('placeholder', config_options.Type(string_types, default=str(SETTINGS['placeholder']))),
        ('decryption_failure_message', config_options.Type(string_types, default=str(SETTINGS['decryption_failure_message']))),
        ('encryption_info_message', config_options.Type(string_types, default=str(SETTINGS['encryption_info_message']))),
        ('password_button_text', config_options.Type(string_types, default=str(SETTINGS['password_button_text']))),
        ('password_button', config_options.Type(bool, default=False)),
        ('input_class', config_options.Type(string_types, default=None)),
        ('button_class', config_options.Type(string_types, default=None)),
        # password feature
        ('global_password', config_options.Type(string_types, default=None)),
        ('use_secret', config_options.Type(string_types, default=None)),
        ('ignore_missing_secret', config_options.Type(bool, default=False)),
        ('remember_password', config_options.Type(bool, default=False)),
        ('session_storage', config_options.Type(bool, default=True)),
        # default features enabled
        ('arithmatex', config_options.Type(bool, default=True)),
        ('hljs', config_options.Type(bool, default=True)),
        ('mermaid2', config_options.Type(bool, default=True)),
        ('tag_encrypted_page', config_options.Type(bool, default=True)),
        # override feature
        ('html_template_path', config_options.Type(string_types, default=str(os.path.join(PLUGIN_DIR, 'decrypt-form.tpl.html')))),
        ('html_extra_vars', config_options.Type(dict, default={})),
        ('js_template_path', config_options.Type(string_types, default=str(os.path.join(PLUGIN_DIR, 'decrypt-contents.tpl.js')))),
        ('js_extra_vars', config_options.Type(dict, default={})),
        # others features
        ('encrypted_something', config_options.Type(dict, default={})),
        ('search_index', config_options.Choice(('clear', 'dynamically', 'encrypted'), default='encrypted')),
        ('reload_scripts', config_options.Type(list, default=[])),
        ('inject', config_options.Type(dict, default={})),
        ('selfhost', config_options.Type(bool, default=False)),
        ('selfhost_download', config_options.Type(bool, default=True)),
        ('selfhost_dir', config_options.Type(string_types, default='')),
        ('translations', config_options.Type(dict, default={}, required=False)),
        ('hash_filenames', config_options.Type(dict, default={}, required=False)),
        ('kdf_pow', config_options.Type(int, default=int(5))),
        # legacy features, doesn't exist anymore
    )

    setup = {}

    def __hash_md5_file__(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def __download_and_check__(self, filename, url, hash):
        hash_md5 = hashlib.md5()
        if not exists(filename):
            with urlopen(url) as response:
                filecontent = response.read()
                hash_md5.update(filecontent)
                hash_check = hash_md5.hexdigest()
                if hash == hash_check:
                    with open(filename, 'wb') as file:
                        file.write(filecontent)
                        logger.info('Downloaded external asset "' + filename.name + '"')
                else:
                    logger.error('Error downloading asset "' + filename.name + '" hash mismatch!')
                    os._exit(1)

    def __encrypt_key__(self, key, password):
        """ Encrypts key with PBKDF2 and AES-256. """
        salt = get_random_bytes(16)
        iv = get_random_bytes(16)
        # key must be 32 bytes for AES-256, so the password is hashed with md5 first
        iterations = self.setup['kdf_iterations'] if not key[1] else 1
        kdfkey = PBKDF2(password, salt, 32, count=iterations, hmac_hash_module=SHA256)
        cipher = AES.new(kdfkey, AES.MODE_CBC, iv)
        plaintext = key[0]
        # plaintext must be padded to be a multiple of BLOCK_SIZE
        plaintext_padded = pad(plaintext, 16, style='pkcs7')
        ciphertext = cipher.encrypt(plaintext_padded)
        return (
            base64.b64encode(iv),
            base64.b64encode(ciphertext),
            base64.b64encode(salt)
        )

    def __encrypt_text__(self, text, password):
        """ Encrypts text with AES-256. """
        iv = get_random_bytes(16)
        key = self.setup['keystore'][password][0]
        # key must be 32 bytes for AES-256, so the password is hashed with md5 first
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = text.encode('utf-8')
        # plaintext must be padded to be a multiple of BLOCK_SIZE
        plaintext_padded = pad(plaintext, 16, style='pkcs7')
        ciphertext = cipher.encrypt(plaintext_padded)
        return (
            base64.b64encode(iv),
            base64.b64encode(ciphertext),
        )

    def __encrypt_content__(self, content, base_path, encryptcontent_path, encryptcontent):
        """ Replaces page or article content with decrypt form. """
        ciphertext_bundle = self.__encrypt_text__(content, encryptcontent['password'])

        # optionally selfhost cryptojs
        js_libraries = []
        for jsurl in JS_LIBRARIES:
            if self.config["selfhost"]:
                js_libraries.append(base_path + 'assets/javascripts/cryptojs/' + jsurl[0].rsplit('/',1)[1])
            else:
                js_libraries.append(jsurl[0])

        obfuscate = 1 if encryptcontent.get('obfuscate') else 0
        if obfuscate:
            obfuscate_password = encryptcontent['password']
        else:
            obfuscate_password = None

        encryptcontent_keystore = self.__encrypt_key__(self.setup['keystore'][encryptcontent['password']], encryptcontent['password'])

        decrypt_form = Template(self.setup['html_template']).render({
            # custom message and template rendering
            'summary': encryptcontent['summary'],
            'placeholder': encryptcontent['placeholder'],
            'password_button': self.config['password_button'],
            'password_button_text': encryptcontent['password_button_text'],
            'encryption_info_message': encryptcontent['encryption_info_message'],
            'decryption_failure_message': json.dumps(encryptcontent['decryption_failure_message']),
            'input_class': self.config['input_class'],
            'button_class': self.config['button_class'],
            'obfuscate': obfuscate,
            'obfuscate_password': obfuscate_password,
            # this benign decoding is necessary before writing to the template,
            # otherwise the output string will be wrapped with b''
            'ciphertext_bundle': b';'.join(ciphertext_bundle).decode('ascii'),
            'js_libraries': js_libraries,
            'base_path': base_path,
            'encryptcontent_path': encryptcontent_path,
            'encryptcontent_keystore': '"' + b';'.join(encryptcontent_keystore).decode('ascii') + '"',
            # add extra vars
            'extra': self.config['html_extra_vars']
        })
        return decrypt_form

    def __generate_decrypt_js__(self):
        """ Generate JS file with enable feature. """
        decrypt_js = Template(self.setup['js_template']).render({
            # custom message and template rendering
            'password_button': self.config['password_button'],
            # enable / disable features
            'arithmatex': self.config['arithmatex'],
            'hljs': self.config['hljs'],
            'mermaid2': self.config['mermaid2'],
            'remember_password': self.config['remember_password'],
            'session_storage': self.config['session_storage'],
            'encrypted_something': self.setup['encrypted_something'],
            'reload_scripts': self.config['reload_scripts'],
            'experimental': self.config['search_index'] == 'dynamically',
            'site_path': self.setup['site_path'],
            'kdf_iterations' : self.setup['kdf_iterations'],
            # add extra vars
            'extra': self.config['js_extra_vars']
        })
        return decrypt_js

    def __get_entropy_from_password__(self, password):
        #          123456789012345678901234567890
        lcase =   "abcdefghijklmnopqrstuvwxyz"
        ucase =   "ABCDEFGHIJKLMNOPQRTSUVWXYZ"
        number =  "0123456789"
        special = "!*#,;?+-_.=~^%()[]{}|:/"
        other = ""
        lcase_used = False
        ucase_used = False
        number_used = False
        special_used = False
        other_used = 0
        for character in password:
            if character in lcase:
                lcase_used = True
            elif character in ucase:
                ucase_used = True
            elif character in number:
                number_used = True
            elif character in special:
                special_used = True
            elif character not in other:
                other_used += 1
                other += character
        ent = 0
        if lcase_used:
            ent += len(lcase)
        if ucase_used:
            ent += len(ucase)
        if number_used:
            ent += len(number)
        if special_used:
            ent += len(special)
        ent += other_used
        ent_max = len(lcase) + len(ucase) + len(number) + len(special) + len(other)
        enttropy_spied_on = math.log( pow(ent, len(password)) ) / math.log(2)
        enttropy_secret = math.log( pow(ent_max, len(password)) ) / math.log(2)
        return enttropy_spied_on, enttropy_secret

    # MKDOCS Events builds

    def on_config(self, config, **kwargs):
        """
        The config event is the first event called on build and is run immediately after the user
        configuration is loaded and validated. Any alterations to the config should be made here.
        Configure plugin self.config from configuration file (mkdocs.yml)

        :param config: global configuration object (mkdocs.yml)
        :return: global configuration object modified to include templates files
        """
        # Override default template
        logger.debug('Load HTML template from file: "{file}".'.format(file=str(self.config['html_template_path'])))
        with open(self.config['html_template_path'], 'r') as template_html:
            self.setup['html_template'] = template_html.read()
        logger.debug('Load JS template from file: "{file}".'.format(file=str(self.config['js_template_path'])))
        with open(self.config['js_template_path'], 'r') as template_js:
            self.setup['js_template'] = template_js.read()

        # Optionnaly use Github secret
        if self.config.get('use_secret'):
            if os.environ.get(str(self.config['use_secret'])):
                self.config['global_password'] = os.environ.get(str(self.config['use_secret']))
            else:
                if self.config['ignore_missing_secret'] and self.config['global_password']:
                    logger.warning('Cannot get global password from environment variable: {var}. Using global_password as fallback!'.format(
                        var=str(self.config['use_secret']))
                    )
                else:
                    logger.error('Cannot get global password from environment variable: {var}. Abort !'.format(
                        var=str(self.config['use_secret']))
                    )
                    os._exit(1)                                 # prevent build without password to avoid leak

        # Check if hljs feature need to be enabled, based on theme configuration
        if ('highlightjs' in config['theme']._vars
                and config['theme']._vars['highlightjs']    # noqa: W503
                    and self.config['hljs'] is not False):  # noqa: W503, E127
            logger.debug('"highlightjs" value detected on theme config, enable rendering after decryption.')
            self.config['hljs'] = config['theme']._vars['highlightjs']
        else:
            logger.info('"highlightjs" feature is disabled in your plugin configuration.')
            self.config['hljs'] = False
        # Check if pymdownx.arithmatex feature need to be enabled, based on markdown_extensions configuration
        if ('pymdownx.arithmatex' in config['markdown_extensions']
                and self.config['arithmatex'] is not False):  # noqa: W503
            logger.debug('"arithmatex" value detected on extensions config, enable rendering after decryption.')
            self.config['arithmatex'] = True
        else:
            logger.info('"arithmatex" feature is disabled in your plugin configuration.')
            self.config['arithmatex'] = False
        # Check if mermaid feature need to be enabled, based on plugin configuration
        if config['plugins'].get('mermaid2') and self.config['mermaid2'] is not False:
            logger.debug('"mermaid2" value detected on extensions config, enable rendering after decryption.')
            self.config['mermaid2'] = True
        else:
            logger.info('"mermaid2" feature is disabled in your plugin configuration.')
            self.config['mermaid2'] = False
        # Warn about deprecated features on Version 3.0.0
        deprecated_options_detected = False
        if self.config.get('default_expire_delay'):
            logger.warning('DEPRECATED: Feature "default_expire_delay" is no longer supported. Can be removed.')
            deprecated_options_detected = True
        if deprecated_options_detected:
            logger.warning('DEPRECATED: Features marked as deprecated will be remove in next minor version !')
        # Enable experimental code .. :popcorn:
        if self.config['search_index'] == 'dynamically':
            logger.info("EXPERIMENTAL search index encryption enabled.")
        self.setup['encrypted_something'] = {**self.config['inject'], **self.config['encrypted_something']} #add inject to encrypted_something
        # Get path to site in case of subdir in site_url
        self.setup['site_path'] = urlsplit(config.data["site_url"] or '/').path[1::]

        self.setup['search_plugin_found'] = False
        encryptcontent_plugin_found = False
        for plugin in config['plugins']:
            if plugin.endswith('search'):
                if encryptcontent_plugin_found:
                    logger.error('Plugins need to be reordered ("search" ahead of "encryptcontent" in the end)! Otherwise search index might leak sensitive data.')
                    os._exit(1) # prevent build without search index modification
                self.setup['search_plugin_found'] = True
            if plugin == 'encryptcontent':
                encryptcontent_plugin_found = True
        if not self.setup['search_plugin_found']:
            logger.warning('"search" plugin wasn\'t enabled. Search index isn\'t generated or modified.')

        self.setup['locations'] = {}

        self.setup['kdf_iterations'] = pow(10,self.config['kdf_pow'])

        self.setup['keystore'] = {}

    def on_pre_build(self, config, **kwargs):
        """
        The pre_build event does not alter any variables. Use this event to call pre-build scripts.
        Overwrite default mkdocs-search contrib plugin with experimental one for work with
        encrypted search index.

        :param config: global configuration object (mkdocs.yml)
        """
        # Overwrite SearchPlugin function to encrypt search_index if not disable on_pre_build hook
        # event is used by search plugin to initialize an index this modified function is used to
        # encrypt 'text' fields of search_index.
        # ref: https://github.com/mkdocs/mkdocs/tree/master/mkdocs/contrib/search
        try:
            #search_index encryption was moved to on_post_page
            if self.config['search_index'] == 'dynamically':
                if config['theme'].name == 'material':
                    logger.warning("To enable EXPERIMENTAL search index decryption mkdocs-material needs to be customized (patched)!")
                else:
                    # Overwrite search/*.js files from templates/search with encryptcontent contrib search assets
                    for dir in config['theme'].dirs.copy():
                        if re.compile(r".*[/\\]contrib[/\\]search[/\\]templates$").match(dir):
                            config['theme'].dirs.remove(dir)
                            path = os.path.join(base_path, 'contrib/templates')
                            config['theme'].dirs.append(path)
                            if 'search/main.js' not in config['extra_javascript']:
                                config['extra_javascript'].append('search/main.js')
                            break
        except Exception as exp:
            logger.exception(exp)

        # optionally download cryptojs
        if self.config['selfhost'] and self.config['selfhost_download']:
            logger.info('Downloading cryptojs for self-hosting (if needed)...')
            if self.config['selfhost_dir']:
                configpath = Path(config['config_file_path']).parents[0]
                dlpath = configpath.joinpath(self.config['selfhost_dir'] + '/assets/javascripts/cryptojs/')
            else:
                dlpath = Path(config.data['docs_dir'] + '/assets/javascripts/cryptojs/')
            dlpath.mkdir(parents=True, exist_ok=True)
            for jsurl in JS_LIBRARIES:
                dlurl = "https:" + jsurl[0]
                filepath = dlpath.joinpath(jsurl[0].rsplit('/',1)[1])
                self.__download_and_check__(filepath, dlurl, jsurl[1])

    def on_files(self, files, config, **kwargs):
        """
        The files event is called after the files collection is populated from the docs_dir.
        Use this event to add, remove, or alter files in the collection.
        Note that Page objects have not yet been associated with the file objects in the collection.
        Use Page Events to manipulate page specific data.
        """
        if 'extensions' in self.config['hash_filenames']:
            for file in files:

                if 'except' in self.config['hash_filenames']:
                    skip = False
                    for check in self.config['hash_filenames']['except']:
                        if file.src_path.endswith(check):
                            skip = True
                    if skip:
                        continue

                ext = file.src_path.rsplit('.',1)[1].lower()
                if ext in self.config['hash_filenames']['extensions']:
                    hash = self.__hash_md5_file__(file.abs_src_path)
                    filename, ext =  file.abs_dest_path.rsplit('.',1)
                    filename = filename + "_" + hash
                    file.abs_dest_path = filename + "." + ext
                    filename, ext =  file.url.rsplit('.',1)
                    filename = filename + "_" + hash
                    file.url = filename + "." + ext

    def on_page_markdown(self, markdown, page, config, **kwargs):
        """
        The page_markdown event is called after the page's markdown is loaded from file and
        can be used to alter the Markdown source text. The meta- data has been stripped off
        and is available as page.meta at this point.
        Load password from meta header *.md pages and override global_password if defined.

        :param markdown: Markdown source text of page as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :param site_navigation: global navigation object
        :return: Markdown source text of page as string
        """

        encryptcontent = {} #init page data dict

        # Set global password as default password for each page
        encryptcontent['password'] = self.config['global_password']

        if 'password' in page.meta.keys():
            # If global_password is set, but you don't want to encrypt content
            page_password = str(page.meta.get('password'))
            encryptcontent['password'] = None if page_password == '' else page_password
            # Delete meta password information before rendering to avoid leak :]
            del page.meta['password']

        if 'use_secret' in page.meta.keys():
            if os.environ.get(str(page.meta.get('use_secret'))):
                encryptcontent['password'] = os.environ.get(str(page.meta.get('use_secret')))
            else:
                if self.config['ignore_missing_secret'] and encryptcontent['password']:
                    logger.warning('Cannot get password for "{page}" from environment variable: {var}. Using password from config or meta key as fallback!'.format(
                        var=str(page.meta.get('use_secret')), page=page.title)
                    )
                else:
                    logger.error('Cannot get password for "{page}" from environment variable: {var}. Abort !'.format(
                        var=str(page.meta.get('use_secret')), page=page.title)
                    )
                    os._exit(1)                                 # prevent build without password to avoid leak0

        if 'obfuscate' in page.meta.keys():
            if encryptcontent['password'] is None: # Only allow obfuscation if no password defined
                encryptcontent['obfuscate'] = True
                encryptcontent['password'] = str(page.meta.get('obfuscate'))
            del page.meta['obfuscate']

        if encryptcontent.get('password'):
            # Custom per-page strings
            if 'encryption_summary' in page.meta.keys():
                encryptcontent['summary'] = str(page.meta.get('encryption_summary'))
                del page.meta['encryption_summary']

            if 'encryption_info_message' in page.meta.keys():
                encryptcontent['encryption_info_message'] = str(page.meta.get('encryption_info_message'))
                del page.meta['encryption_info_message']

            if encryptcontent['password'] not in self.setup['keystore']:
                self.setup['keystore'][encryptcontent['password']] = [get_random_bytes(32), encryptcontent.get('obfuscate')]

            setattr(page, 'encryptcontent', encryptcontent)

        return markdown

    def on_page_content(self, html, page, config, **kwargs):
        """
        The page_content event is called after the Markdown text is rendered to HTML (but before
        being passed to a template) and can be used to alter the HTML body of the page. Generate
        encrypt content with AES and add form to decrypt this content with JS. Keep the generated
        value in a temporary attribute for the search work on clear version of content.

        :param html: HTML rendered from Markdown source as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :param site_navigation: global navigation object
        :return: HTML rendered from Markdown source as string encrypt with AES
        """

        if hasattr(page, 'encryptcontent'):
            if self.config['tag_encrypted_page']:
                # Set attribute on page to identify encrypted page on template rendering
                setattr(page, 'encrypted', True)

            # Keep encrypted html to encrypt as temporary variable on page
            if not self.config['inject']:
                page.encryptcontent['html_to_encrypt'] = html

        return html

    def on_page_context(self, context, page, config, **kwargs):
        """
        The page_context event is called after the context for a page is created and
        can be used to alter the context for that specific page only.
        Replace clear HTML content with encrypted content and remove temporary attribute.
        Perform this step AFTER the search plugin have create a set of entries in the index.

        :param context: dict of template context variables
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :param nav: global navigation object
        :return: dict of template context variables
        """
        if hasattr(page, 'encryptcontent'):
            if 'i18n_page_file_locale' in context:
                locale = context['i18n_page_file_locale']
                if locale in self.config['translations']:
                    translations = self.config['translations'][locale]

                    #apply translation if defined
                    if 'title_prefix' in translations and 'title_prefix' not in page.encryptcontent:
                        page.encryptcontent['title_prefix'] = translations['title_prefix']
                    if 'summary' in translations and 'summary' not in page.encryptcontent:
                        page.encryptcontent['summary'] = translations['summary']
                    if 'placeholder' in translations and 'placeholder' not in page.encryptcontent:
                        page.encryptcontent['placeholder'] = translations['placeholder']
                    if 'password_button_text' in translations and 'password_button_text' not in page.encryptcontent:
                        page.encryptcontent['password_button_text'] = translations['password_button_text']
                    if 'decryption_failure_message' in translations and 'decryption_failure_message' not in page.encryptcontent:
                        page.encryptcontent['decryption_failure_message'] = translations['decryption_failure_message']
                    if 'encryption_info_message' in translations and 'encryption_info_message' not in page.encryptcontent:
                        page.encryptcontent['encryption_info_message'] = translations['encryption_info_message']

            #init default strings from config
            if 'title_prefix' not in page.encryptcontent:
                page.encryptcontent['title_prefix'] = self.config['title_prefix']
            if 'summary' not in page.encryptcontent:
                page.encryptcontent['summary'] = self.config['summary']
            if 'placeholder' not in page.encryptcontent:
                page.encryptcontent['placeholder'] = self.config['placeholder']
            if 'password_button_text' not in page.encryptcontent:
                page.encryptcontent['password_button_text'] = self.config['password_button_text']
            if 'decryption_failure_message' not in page.encryptcontent:
                page.encryptcontent['decryption_failure_message'] = self.config['decryption_failure_message']
            if 'encryption_info_message' not in page.encryptcontent:
                page.encryptcontent['encryption_info_message'] = self.config['encryption_info_message']

            if page.encryptcontent['title_prefix']: 
                page.title = str(self.config['title_prefix']) + str(page.title)

            if 'html_to_encrypt' in page.encryptcontent:
                page.content = self.__encrypt_content__(
                    page.encryptcontent['html_to_encrypt'], 
                    context['base_url']+'/',
                    self.setup['site_path']+page.url,
                    page.encryptcontent
                )
                page.encryptcontent['html_to_encrypt'] = None

            if self.config['inject']:
                page.encryptcontent['decrypt_form'] = self.__encrypt_content__(
                    '<!-- dummy -->', 
                    context['base_url']+'/',
                    self.setup['site_path']+page.url,
                    page.encryptcontent
                )

        return context

    def on_post_page(self, output_content, page, config, **kwargs):
        """
        The post_page event is called after the template is rendered, but before it is written to
        disc and can be used to alter the output of the page. If an empty string is returned, the
        page is skipped and nothing is written to disc. Finds other parts of HTML that need to be
        encrypted and replaces the content with a protected version.

        :param output_content: output of rendered template as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :return: output of rendered template as string
        """
        # Limit this process only if encrypted_something feature is enable *(speedup)*
        if (self.setup['encrypted_something'] and hasattr(page, 'encryptcontent')
                and len(self.setup['encrypted_something']) > 0):  # noqa: W503
            soup = BeautifulSoup(output_content, 'html.parser')
            for name, tag in self.setup['encrypted_something'].items():
                # logger.debug({'name': name, 'html tag': tag[0], 'type': tag[1]})
                something_search = soup.findAll(tag[0], {tag[1]: name})
                if something_search is not None and len(something_search) > 0:
                    # Loop for multi child tags on target element
                    for item in something_search:
                        # Remove '\n', ' ' useless content generated by bs4 parsing...
                        item.contents = [
                            content for content in item.contents if content not in ['\n', ' ']
                        ]
                        # Merge the content in case there are several elements
                        if len(item.contents) > 1:
                            merge_item = ''.join([str(s) for s in item.contents])
                        elif len(item.contents) == 1:
                            merge_item = item.contents[0]
                        else:
                            merge_item = ""
                        # Encrypt child items on target tags with page password
                        cipher_bundle = self.__encrypt_text__(merge_item, str(page.encryptcontent['password']))
                        encrypted_content = b';'.join(cipher_bundle).decode('ascii')
                        # Replace initial content with encrypted one
                        item.string = encrypted_content
                        if item.has_attr('style'):
                            if isinstance(item['style'], list):
                                item['style'].append("display:none")
                            else:
                                # if style contains a single element (str)
                                item['style'] = item['style'] + "display:none"
                        else:
                            item['style'] = "display:none"

            if self.config['inject'] and len(self.config['inject']) == 1:
                name, tag = list(self.config['inject'].items())[0]
                injector = soup.new_tag("div")
                something_search = soup.find(tag[0], {tag[1]: name})
                something_search.insert_before(injector)
                injector.append(BeautifulSoup(page.encryptcontent['decrypt_form'], 'html.parser'))
                page.encryptcontent['decrypt_form'] = None

            output_content = str(soup)

        if hasattr(page, 'encryptcontent'):
            location = page.url.lstrip('/')
            self.setup['locations'][location] = page.encryptcontent['password']
            delattr(page, 'encryptcontent')

        return output_content

    def on_post_build(self, config, **kwargs):
        """
        The post_build event does not alter any variables.
        Use this event to call post-build scripts.

        :param config: global configuration object
        """
        Path(config.data["site_dir"] + '/assets/javascripts/').mkdir(parents=True, exist_ok=True)
        decrypt_js_path = Path(config.data["site_dir"] + '/assets/javascripts/decrypt-contents.js')
        with open(decrypt_js_path, "w") as file:
            file.write(self.__generate_decrypt_js__())

        #modify search_index in the style of mkdocs-exclude-search
        if self.setup['search_plugin_found'] and self.config['search_index'] != 'clear':
            search_index_filename = Path(config.data["site_dir"] + "/search/search_index.json")
            try:
                with open(search_index_filename, "r") as f:
                    search_entries = json.load(f)
            except:
                logger.error('Search index needs modification, but could not read "search_index.json"!')
                os._exit(1)

            for entry in search_entries['docs'].copy(): #iterate through all entries of search_index
                for location in self.setup['locations'].keys():
                    if entry['location'] == location or entry['location'].startswith(location+"#"): #find the ones located at encrypted pages
                        page_password = self.setup['locations'][location]
                        if self.config['search_index'] == 'encrypted':
                            search_entries['docs'].remove(entry)
                        elif self.config['search_index'] == 'dynamically' and page_password is not None:
                            #encrypt text/title/location(anchor only)
                            text = entry['text']
                            title = entry['title']
                            toc_anchor = entry['location'].replace(location, '')
                            code = self.__encrypt_text__(text, page_password )
                            entry['text'] = b';'.join(code).decode('ascii')
                            code = self.__encrypt_text__(title, page_password)
                            entry['title'] = b';'.join(code).decode('ascii')
                            code = self.__encrypt_text__(toc_anchor, page_password)
                            entry['location'] = location + ';' + b';'.join(code).decode('ascii')
                        break
            self.setup['locations'].clear()

            try:
                with open(search_index_filename, "w") as f:
                    json.dump(search_entries, f)
            except:
                logger.error('Search index needs modification, but could not write "search_index.json"!')
                os._exit(1)
            logger.info('Modified search_index.')

        min_enttropy_spied_on, min_enttropy_secret = 0, 0
        for password in self.setup['keystore'].keys():
            if not self.setup['keystore'][password][1]:
                enttropy_spied_on, enttropy_secret = self.__get_entropy_from_password__(password)
                if min_enttropy_spied_on == 0 or enttropy_spied_on < min_enttropy_spied_on:
                    min_enttropy_spied_on = enttropy_spied_on
                if min_enttropy_secret == 0 or enttropy_secret < min_enttropy_secret:
                    min_enttropy_secret = enttropy_secret
        self.setup['keystore'].clear()
        if min_enttropy_spied_on < 100 and min_enttropy_spied_on > 0:
            logger.warning('mkdocs-encryptcontent-plugin will always be vulnerable to brute-force attacks!'
                           ' Your weakest password only got {spied_on} bits of entropy, if someone watched you while typing'
                           ' (and a maximum of {secret} bits total)!'.format(spied_on = math.ceil(enttropy_spied_on), secret = math.ceil(min_enttropy_secret))
                    )
