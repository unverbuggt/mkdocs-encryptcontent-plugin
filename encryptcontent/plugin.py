
import os
import re
import base64
import hashlib
import logging
from pathlib import Path
from Crypto import Random
from jinja2 import Template
from Crypto.Cipher import AES
from bs4 import BeautifulSoup
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from urllib.parse import urlsplit

try:
    from mkdocs.utils import string_types
except ImportError:
    string_types = str

JS_LIBRARIES = [
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/core.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/enc-base64.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/cipher-core.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/pad-nopadding.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/md5.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/aes.js'
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
        # password feature
        ('global_password', config_options.Type(string_types, default=None)),
        ('use_secret', config_options.Type(string_types, default=None)),
        ('password', config_options.Type(string_types, default=None)),
        ('remember_password', config_options.Type(bool, default=False)),
        ('session_storage', config_options.Type(bool, default=True)),
        ('default_expire_delay', config_options.Type(int, default=int(24))),
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
        ('experimental', config_options.Type(bool, default=False)),
        ('inject', config_options.Type(dict, default={})),
        # legacy features, doesn't exist anymore
        ('disable_cookie_protection', config_options.Type(bool, default=False)),
        ('decrypt_search', config_options.Type(bool, default=False))
    )

    def __hash_md5__(self, text):
        """ Creates an md5 hash from text. """
        key = hashlib.md5()
        key.update(text.encode('utf-8'))
        return key.digest()

    def __encrypt_text_aes__(self, text, password):
        """ Encrypts text with AES-256. """
        BLOCK_SIZE = 32
        PADDING_CHAR = b'^'
        iv = Random.new().read(16)
        # key must be 32 bytes for AES-256, so the password is hashed with md5 first
        cipher = AES.new(self.__hash_md5__(password), AES.MODE_CBC, iv)
        plaintext = text.encode('utf-8')
        # plaintext must be padded to be a multiple of BLOCK_SIZE
        plaintext_padded = plaintext + (BLOCK_SIZE - len(plaintext) % BLOCK_SIZE) * PADDING_CHAR
        ciphertext = cipher.encrypt(plaintext_padded)
        return (
            base64.b64encode(iv),
            base64.b64encode(ciphertext),
            PADDING_CHAR
        )

    def __encrypt_content__(self, content, password, base_path, encryptcontent_path):
        """ Replaces page or article content with decrypt form. """
        ciphertext_bundle = self.__encrypt_text_aes__(content, password)
        decrypt_form = Template(self.config['html_template']).render({
            # custom message and template rendering
            'summary': self.config['summary'],
            'placeholder': self.config['placeholder'],
            'password_button': self.config['password_button'],
            'password_button_text': self.config['password_button_text'],
            'encryption_info_message': self.config['encryption_info_message'],
            # this benign decoding is necessary before writing to the template,
            # otherwise the output string will be wrapped with b''
            'ciphertext_bundle': b';'.join(ciphertext_bundle).decode('ascii'),
            'js_libraries': JS_LIBRARIES,
            'base_path': base_path,
            'encryptcontent_path': encryptcontent_path,
            # add extra vars
            'extra': self.config['html_extra_vars']
        })
        return decrypt_form

    def __generate_decrypt_js__(self):
        """ Generate JS file with enable feature. """
        decrypt_js = Template(self.config['js_template']).render({
            # custom message and template rendering
            'password_button': self.config['password_button'],
            'decryption_failure_message': self.config['decryption_failure_message'],
            # enable / disable features
            'arithmatex': self.config['arithmatex'],
            'hljs': self.config['hljs'],
            'mermaid2': self.config['mermaid2'],
            'remember_password': self.config['remember_password'],
            'session_storage': self.config['session_storage'],
            'default_expire_delay': int(self.config['default_expire_delay']),
            'encrypted_something': self.config['encrypted_something'],
            'reload_scripts': self.config['reload_scripts'],
            'experimental': self.config['experimental'],
            'site_path': self.config['site_path'],
            # add extra vars
            'extra': self.config['js_extra_vars']
        })
        return decrypt_js

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
            self.config['html_template'] = template_html.read()
        logger.debug('Load JS template from file: "{file}".'.format(file=str(self.config['js_template_path'])))
        with open(self.config['js_template_path'], 'r') as template_js:
            self.config['js_template'] = template_js.read()
        # Optionnaly use Github secret
        if self.config.get('use_secret'):
            if os.environ.get(str(self.config['use_secret'])):
                self.config['global_password'] = os.environ.get(str(self.config['use_secret']))
            else:
                logger.error('Cannot get global password from environment variable: {var}. Abort !'.format(
                    var=str(self.config['use_secret']))
                )
                os._exit(1)                                 # prevent build without password to avoid leak
        # Set global password as default password for each page
        self.config['password'] = self.config['global_password']
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
        # Warn about deprecated features on Vervion 2.0.0
        deprecated_options_detected = False
        if self.config.get('disable_cookie_protection'):
            logger.warning('DEPRECATED: Feature "disable_cookie_protection" is no longer supported. Can by remove.')
            deprecated_options_detected = True
        if self.config.get('decrypt_search'):
            logger.warning('DEPRECATED: Feature "decrypt_search" is no longer supported. Use search_index on "clear" mode instead.')
            deprecated_options_detected = True
            logger.info('Fallback "decrypt_search" configuraiton to "search_index" mode clear.')
            self.config['search_index'] = 'clear'
        if deprecated_options_detected:
            logger.warning('DEPRECATED: Features marked as deprecated will be remove in next minor version !')
        # Re order plugins to be sure search-index are not encrypted
        if self.config['search_index'] == 'clear':
            logger.debug('Reordering plugins loading and put search and encryptcontent at the end of the event pipe.')
            try: #PluginCollection is no instance of OrderedDict anymore since MkDocs 1.4
                config['plugins'].move_to_end('search')
                config['plugins'].move_to_end('encryptcontent')
            except:
                logger.warning('Please check that "search" and "encryptcontent" are at the end of plugins')
        # Enable experimental code .. :popcorn:
        if self.config['search_index'] == 'dynamically':
            logger.info('EXPERIMENTAL MODE ENABLE. Only work with default SearchPlugin, not Material.')
            self.config['experimental'] = True
        self.config['encrypted_something'] = self.config['inject'] | self.config['encrypted_something'] #add inject to encrypted_something
        # Get path to site in case of subdir in site_url
        self.config['site_path'] = urlsplit(config.data["site_url"] or '/').path[1::]

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
            if self.config['experimental'] is True:
                if config['theme'].name == 'material':
                    logger.error("UNSUPPORTED Material theme with experimantal feature search_index=dynamically !")
                    exit("UNSUPPORTED Material theme: use search_index: [clear|encrypted] instead.")
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

    def on_page_markdown(self, markdown, page, config, **kwargs):
        """
        The page_markdown event is called after the page's markdown is loaded from file and
        can be used to alter the Markdown source text. The meta- data has been stripped off
        and is available as page.meta at this point.
        Load password from meta header *.md pages and override global_password if define.

        :param markdown: Markdown source text of page as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :param site_navigation: global navigation object
        :return: Markdown source text of page as string
        """
        self.config['password'] = self.config['global_password']
        if 'password' in page.meta.keys():
            # If global_password is set, but you don't want to encrypt content
            page_password = str(page.meta.get('password'))
            self.config['password'] = None if page_password == '' else page_password
            # Delete meta password information before rendering to avoid leak :]
            del page.meta['password']
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
        if self.config['password'] is not None:
            if self.config['title_prefix']:
                page.title = str(self.config['title_prefix']) + str(page.title)
            if self.config['tag_encrypted_page']:
                # Set attribute on page to identify encrypted page on template rendering
                setattr(page, 'encrypted', True)
            # Set password attributes on page for other mkdocs events
            setattr(page, 'password', str(self.config['password']))
            # Keep encrypted html to encrypt as temporary variable on page
            if not self.config['inject']:
                setattr(page, 'html_to_encrypt', html)
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
        if hasattr(page, 'html_to_encrypt'):
            page.content = self.__encrypt_content__(
                page.html_to_encrypt, 
                str(page.password),
                context['base_url']+'/',
                self.config['site_path']+page.url
            )
            delattr(page, 'html_to_encrypt')
        if self.config['inject']:
            setattr(page, 'decrypt_form', self.__encrypt_content__(
                '<!-- dummy -->', 
                str(page.password),
                context['base_url']+'/',
                self.config['site_path']+page.url
            ))
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
        if (self.config['encrypted_something'] and hasattr(page, 'encrypted')
                and len(self.config['encrypted_something']) > 0):  # noqa: W503
            soup = BeautifulSoup(output_content, 'html.parser')
            for name, tag in self.config['encrypted_something'].items():
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
                        cipher_bundle = self.__encrypt_text_aes__(merge_item, str(page.password))
                        encrypted_content = b';'.join(cipher_bundle).decode('ascii')
                        # Replace initial content with encrypted one
                        bs4_encrypted_content = BeautifulSoup(encrypted_content, 'html.parser')
                        item.contents = [bs4_encrypted_content]
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
                injector.append(BeautifulSoup(page.decrypt_form, 'html.parser'))
                delattr(page, 'decrypt_form')
            output_content = str(soup)

            #encrypt or exclude encrypted pages from search_index.json
            search_entries = config['plugins']['search'].search_index._entries
            for entry in search_entries.copy(): #iterate through all entries of search_index
                location = page.url.lstrip('/')
                if entry['location'] == location or entry['location'].startswith(location+"#"): #find the ones located at encrypted pages
                    if self.config['search_index'] == 'encrypted':
                        search_entries.remove(entry)
                    elif self.config['search_index'] == 'dynamically' and page.password is not None:
                        #encrypt text/title/location(anchor only)
                        text = entry['text']
                        title = entry['title']
                        toc_anchor = entry['location'].replace(location, '')
                        code = self.__encrypt_text_aes__(text, page.password)
                        entry['text'] = b';'.join(code).decode('ascii')
                        code = self.__encrypt_text_aes__(title, page.password)
                        entry['title'] = b';'.join(code).decode('ascii')
                        code = self.__encrypt_text_aes__(toc_anchor, page.password)
                        entry['location'] = location + ';' + b';'.join(code).decode('ascii')
            config['plugins']['search'].search_index._entries = search_entries

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
