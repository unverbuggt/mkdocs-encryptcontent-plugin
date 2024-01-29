
import os
import re
import base64
import logging
import json
import math
import yaml
from mkdocs.utils.yaml import get_yaml_loader, yaml_load
from mkdocs import plugins
from pathlib import Path
from jinja2 import Template
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256, SHA512, MD5
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Random.random import randrange
from Crypto.Util.Padding import pad
from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa
from bs4 import BeautifulSoup
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from urllib.parse import urlsplit, quote
from urllib.request import urlopen

try:
    from mkdocs.utils import string_types
except ImportError:
    string_types = str

CRYPTO_ES_LIBRARIES = [
    ['//cdn.jsdelivr.net/npm/crypto-es@2.1.0/+esm','fd3628cef78b155ff3da3554537e2d76','crypto-es.mjs'],
]

CRYPTO_JS_LIBRARIES = [
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/core.js','b55ae8027253d4d54c4f1ef3b6254646','core.js'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/enc-base64.js','f551ce1340a86e5edbfef4a6aefa798f','enc-base64.js'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/cipher-core.js','b9c2f3c51e3ffe719444390f47c51627','cipher-core.js'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/sha256.js','561d24c90633fb34c13537a330d12786','sha256.js'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/hmac.js','ee162ca0ed3b55dd9b2fe74a3464bb74','hmac.js'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/pbkdf2.js','3f2876e100b991885f606065d1342984','pbkdf2.js'],
    ['//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/aes.js','da81b91b1b57c279c29b3469649d9b86','aes.js'],
]

PLUGIN_DIR = Path(__file__).parent.absolute()

SETTINGS = {
    'title_prefix': '[Protected] ',
    'summary': 'This content is protected with AES encryption. ',
    'placeholder': 'Password',
    'placeholder_user': 'User name',
    'password_button_text': 'Decrypt',
    'decryption_failure_message': 'Invalid password.',
    'encryption_info_message': 'Contact your administrator for access to this page.'
}

logger = logging.getLogger("mkdocs.plugins.encryptcontent")

KS_OBFUSCATE = -1
KS_PASSWORD = 0

class encryptContentPlugin(BasePlugin):
    """ Plugin that encrypt markdown content with AES and inject decrypt form. """

    config_scheme = (
        # default customization
        ('title_prefix', config_options.Type(string_types, default=str(SETTINGS['title_prefix']))),
        ('summary', config_options.Type(string_types, default=str(SETTINGS['summary']))),
        ('placeholder', config_options.Type(string_types, default=str(SETTINGS['placeholder']))),
        ('placeholder_user', config_options.Type(string_types, default=str(SETTINGS['placeholder_user']))),
        ('decryption_failure_message', config_options.Type(string_types, default=str(SETTINGS['decryption_failure_message']))),
        ('encryption_info_message', config_options.Type(string_types, default=str(SETTINGS['encryption_info_message']))),
        ('password_button_text', config_options.Type(string_types, default=str(SETTINGS['password_button_text']))),
        ('password_button', config_options.Type(bool, default=False)),
        ('form_class', config_options.Type(string_types, default=None)),
        ('input_class', config_options.Type(string_types, default=None)),
        ('button_class', config_options.Type(string_types, default=None)),
        # password feature
        ('global_password', config_options.Type(string_types, default=None)),
        ('remember_keys', config_options.Type(bool, default=True)),
        ('remember_password', config_options.Type(bool, default=False)),
        ('remember_prefix', config_options.Type(string_types, default='encryptcontent_')),
        ('session_storage', config_options.Type(bool, default=True)),
        ('password_inventory', config_options.Type(dict, default={})),
        ('password_file', config_options.Type(string_types, default=None)),
        ('additional_storage_file', config_options.Type(string_types, default=None)),
        ('cache_file', config_options.Type(string_types, default='encryptcontent.cache')),
        ('sharelinks', config_options.Type(bool, default=False)),
        ('sharelinks_incomplete', config_options.Type(bool, default=False)),
        ('sharelinks_output', config_options.Type(string_types, default='sharelinks.txt')),
        # default features enabled
        ('arithmatex', config_options.Type(bool, default=None)),
        ('hljs', config_options.Type(bool, default=None)),
        ('mermaid2', config_options.Type(bool, default=None)),
        ('tag_encrypted_page', config_options.Type(bool, default=True)),
        # override feature
        ('html_template_path', config_options.Type(string_types, default=None)),
        ('html_extra_vars', config_options.Type(dict, default={})),
        ('js_template_path', config_options.Type(string_types, default=None)),
        ('js_extra_vars', config_options.Type(dict, default={})),
        ('canary_template_path', config_options.Type(string_types, default=None)),
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
        ('kdf_pow', config_options.Type(int, default=int(-1))), # -1: default on whether webcrypto is set or not
        ('sign_files', config_options.Type(string_types, default=None)),
        ('sign_key', config_options.Type(string_types, default='encryptcontent.key')),
        ('webcrypto', config_options.Type(bool, default=False)),
        ('esm', config_options.Type(bool, default=False)),
        ('insecure_test', config_options.Type(bool, default=False)), # insecure test build
        # legacy features
    )

    setup = {}

    def __hash_md5_file__(self, fname):
        hash_md5 = MD5.new()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def __download_and_check__(self, filename, url, hash):
        hash_md5 = MD5.new()
        if not Path(filename).exists():
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

    def __sign_file__(self, fname, url, key):
        h = SHA512.new()
        if fname:
            with open(fname, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    h.update(chunk)
        else:
            with urlopen(url) as response:
                h.update(response.read())
        signer = eddsa.new(key, 'rfc8032')
        return base64.b64encode(signer.sign(h)).decode()

    def __add_to_keystore__(self, index, key, id):
        keystore = self.setup['keystore']
        store_id = id

        if index not in keystore:
            new_entry = {}
            new_entry[store_id] = key.hex()
            keystore[index] = new_entry
        else:
            keystore[index][store_id] = key.hex()

    def __vars_to_keystore__(self, index, var, value):
        keystore = self.setup['keystore']
        keystore[index][var] = value

    def __encrypt_keys_from_keystore__(self, index, plaintext_length=-1):
        keystore = self.setup['keystore']
        password = index[1]
        password_hash = SHA256.new(password.encode()).digest().hex() # sha256 sum of password
        if index[0] == KS_OBFUSCATE:
            iterations = 1
        else:
            iterations = self.setup['kdf_iterations']
        """ Encrypts key with PBKDF2 and AES-256. """
        if self.config['insecure_test']:
            salt = bytes([0x20, 0xd4, 0x84, 0x09, 0x44, 0x44, 0x76, 0x89, 0xed, 0x0c, 0xe3, 0x53, 0x76, 0x89, 0xed, 0xdb])
        else:
            salt = get_random_bytes(16)

        regenerate_kdf = True
        if index[0] == KS_OBFUSCATE and password in self.setup['cache']['obfuscate']:
            fromcache = self.setup['cache']['obfuscate'][password].split(';')
            if len(fromcache) == 3 and password_hash == fromcache[2]:
                kdfkey = bytes.fromhex(fromcache[0])
                salt = bytes.fromhex(fromcache[1])
                regenerate_kdf = False
        elif index[0] == KS_PASSWORD and password in self.setup['cache']['password']:
            fromcache = self.setup['cache']['password'][password].split(';')
            if len(fromcache) == 3 and password_hash == fromcache[2]:
                kdfkey = bytes.fromhex(fromcache[0])
                salt = bytes.fromhex(fromcache[1])
                regenerate_kdf = False
        elif isinstance(index[0], str) and index[0] in self.setup['cache']['userpass']:
            fromcache = self.setup['cache']['userpass'][index[0]].split(';')
            if len(fromcache) == 3 and password_hash == fromcache[2]:
                kdfkey = bytes.fromhex(fromcache[0])
                salt = bytes.fromhex(fromcache[1])
                regenerate_kdf = False

        if regenerate_kdf:
            # generate PBKDF2 key from salt and password (password is URI encoded)
            kdfkey = PBKDF2(quote(password, safe='~()*!\''), salt, 32, count=iterations, hmac_hash_module=SHA256)
            logger.info('Need to generate KDF key...')
            if index[0] == KS_OBFUSCATE:
                self.setup['cache']['obfuscate'][password] = kdfkey.hex() + ';' + salt.hex() + ';' + password_hash
            elif index[0] == KS_PASSWORD:
                self.setup['cache']['password'][password] = kdfkey.hex() + ';' + salt.hex() + ';' + password_hash
            else:
                self.setup['cache']['userpass'][index[0]] = kdfkey.hex() + ';' + salt.hex() + ';' + password_hash

        # initialize AES-256
        if self.config['insecure_test']:
            iv = bytes([0x20, 0xd4, 0x84, 0x09, 0x44, 0x44, 0x76, 0x89, 0xed, 0x0c, 0xe3, 0x53, 0x76, 0x89, 0xed, 0xdb])
        else:
            iv = get_random_bytes(16)
        cipher = AES.new(kdfkey, AES.MODE_CBC, iv)
        # use it to encrypt the AES-256 key(s)
        plaintext = json.dumps(keystore[index])
        # add spaces to plaintext to make keystores indistinguishable
        if len(plaintext) < plaintext_length:
            plaintext += ' ' * (plaintext_length - len(plaintext))
        plaintext_encoded = plaintext.encode()
        # plaintext must be padded to be a multiple of 16 bytes
        plaintext_padded = pad(plaintext_encoded, 16, style='pkcs7')
        ciphertext = cipher.encrypt(plaintext_padded)

        if iterations > 1: #don't calculate entropy for obfuscate passwords
            enttropy_spied_on, enttropy_secret = self.__get_entropy_from_password__(password)
            if self.setup['min_enttropy_spied_on'] == 0 or enttropy_spied_on < self.setup['min_enttropy_spied_on']:
                self.setup['min_enttropy_spied_on'] = enttropy_spied_on
            if self.setup['min_enttropy_secret'] == 0 or enttropy_secret < self.setup['min_enttropy_secret']:
                self.setup['min_enttropy_secret'] = enttropy_secret

        if isinstance(index[0], str):
            userhash = quote(index[0].lower(), safe='~()*!\'').encode() # safe transform username analogous to encodeURIComponent
            userhash = SHA256.new(userhash).digest() # sha256 sum of username
            return (
                base64.b64encode(iv).decode() ,
                base64.b64encode(ciphertext).decode(),
                base64.b64encode(salt).decode(),
                base64.b64encode(userhash).decode() # base64 encode userhash
            )
        else:
            return (
                base64.b64encode(iv).decode() ,
                base64.b64encode(ciphertext).decode(),
                base64.b64encode(salt).decode()
            )

    def __encrypt_text__(self, text, key):
        """ Encrypts text with AES-256. """
        # initialize AES-256
        if self.config['insecure_test']:
            iv = bytes([0x20, 0xd4, 0x84, 0x09, 0x44, 0x44, 0x76, 0x89, 0xed, 0x0c, 0xe3, 0x53, 0x76, 0x89, 0xed, 0xdb])
        else:
            iv = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = text.encode('utf-8')
        # plaintext must be padded to be a multiple of 16 bytes
        plaintext_padded = pad(plaintext, 16, style='pkcs7')
        ciphertext = cipher.encrypt(plaintext_padded)
        return (
            base64.b64encode(iv).decode(),
            base64.b64encode(ciphertext).decode(),
        )

    def __encrypt_content__(self, content, base_path, encryptcontent_path, encryptcontent):
        """ Replaces page or article content with decrypt form. """
        
        # optionally selfhost cryptojs
        js_libraries = []
        if not self.config['webcrypto']:
            for jsurl in self.setup['js_libraries']:
                if self.config["selfhost"]:
                    js_libraries.append(base_path + 'assets/javascripts/cryptojs/' + jsurl[2])
                else:
                    js_libraries.append(jsurl[0])

        obfuscate = 0
        uname = 0
        obfuscate_password = None
        encryptcontent_id = ''

        encryptcontent_keystore = []

        if encryptcontent['type'] == 'password':
            # get 32-bit AES-256 key from password_keys
            key = encryptcontent['key']
            keystore = self.setup['password_keys'][encryptcontent['password']]
            encryptcontent_id = keystore['id']
            encryptcontent_keystore.append(self.setup['keystore_password'][(KS_PASSWORD, encryptcontent['password'])])
        elif encryptcontent['type'] == 'level':
            # get 32-bit AES-256 key from level_keys
            key = encryptcontent['key']
            keystore = self.setup['level_keys'][encryptcontent['level']]
            encryptcontent_id = keystore['id']
            if keystore.get('uname'):
                encrypted_keystore = self.setup['keystore_userpass']
                for entry in encrypted_keystore: # might as well add all credentials as keystore can be found by user name
                    encryptcontent_keystore.append(encrypted_keystore[entry])
                uname = 1
            else:
                encrypted_keystore = self.setup['keystore_password']
                for entry in encrypted_keystore:
                    if entry[1] in self.setup['password_inventory'][encryptcontent['level']]:
                        encryptcontent_keystore.append(encrypted_keystore[entry])
        elif encryptcontent['type'] == 'obfuscate':
            # get 32-bit AES-256 key from obfuscate_keys
            key = encryptcontent['key']
            keystore = self.setup['obfuscate_keys'][encryptcontent['obfuscate']]
            encryptcontent_id = keystore['id']
            encryptcontent_keystore.append(self.setup['keystore_obfuscate'][(KS_OBFUSCATE, encryptcontent['obfuscate'])])
            obfuscate = 1
            obfuscate_password = encryptcontent['obfuscate']


        inject_something = encryptcontent['inject'] if 'inject' in encryptcontent else None
        delete_something = encryptcontent['delete_id'] if 'delete_id' in encryptcontent else None

        ciphertext_bundle = self.__encrypt_text__(content, key)

        decrypt_form = Template(self.setup['html_template']).render({
            # custom message and template rendering
            'summary': encryptcontent['summary'],
            'placeholder': encryptcontent['placeholder'],
            'placeholder_user': encryptcontent['placeholder_user'],
            'password_button': self.config['password_button'],
            'password_button_text': encryptcontent['password_button_text'],
            'encryption_info_message': encryptcontent['encryption_info_message'],
            'decryption_failure_message': json.dumps(encryptcontent['decryption_failure_message']),
            'form_class': self.config['form_class'],
            'input_class': self.config['input_class'],
            'button_class': self.config['button_class'],
            'uname': uname,
            'obfuscate': obfuscate,
            'obfuscate_password': obfuscate_password,
            'ciphertext_bundle': ';'.join(ciphertext_bundle),
            'js_libraries': js_libraries,
            'base_path': base_path,
            'encryptcontent_id': encryptcontent_id,
            'encryptcontent_path': encryptcontent_path,
            'encryptcontent_keystore': json.dumps(encryptcontent_keystore),
            'inject_something': inject_something,
            'delete_something': delete_something,
            'webcrypto' : self.config['webcrypto'],
            'esm' : self.config['esm'],
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
            'remember_keys': self.config['remember_keys'],
            'remember_password': self.config['remember_password'],
            'session_storage': self.config['session_storage'],
            'encrypted_something': self.config['encrypted_something'],
            'reload_scripts': self.config['reload_scripts'],
            'experimental': self.config['search_index'] == 'dynamically',
            'site_path': self.setup['site_path'],
            'kdf_iterations' : self.setup['kdf_iterations'],
            'webcrypto' : self.config['webcrypto'],
            'esm' : self.config['esm'],
            'remember_prefix': quote(self.config['remember_prefix'], safe='~()*!\''),
            'sharelinks' : self.config['sharelinks'],
            'sharelinks_incomplete' : self.config['sharelinks_incomplete'],
            'material' : self.setup['theme'] == 'material',
            # add extra vars
            'extra': self.config['js_extra_vars']
        })
        return decrypt_js

    def __b64url_encode__(self, input):
        return base64.b64encode(input.encode(), altchars=b'-_').decode().replace('=','')

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
        self.setup['config_path'] = Path(config['config_file_path']).parent

        self.setup['theme'] = config['theme'].name

        # set default templates or override relative to mkdocs.yml
        if not self.config['html_template_path']:
            html_template_path = PLUGIN_DIR.joinpath('decrypt-form.tpl.html')
        else:
            html_template_path = self.setup['config_path'].joinpath(self.config['html_template_path'])

        if not self.config['js_template_path']:
            js_template_path = PLUGIN_DIR.joinpath('decrypt-contents.tpl.js')
        else:
            js_template_path = self.setup['config_path'].joinpath(self.config['js_template_path'])

        if not self.config['canary_template_path']:
            canary_template_path = PLUGIN_DIR.joinpath('canary.tpl.py')
        else:
            canary_template_path = self.setup['config_path'].joinpath(self.config['canary_template_path'])

        logger.debug('Load HTML template from file: "{file}".'.format(file=html_template_path))
        with open(html_template_path, 'r') as template_html:
            self.setup['html_template'] = template_html.read()
        logger.debug('Load JS template from file: "{file}".'.format(file=js_template_path))
        with open(js_template_path, 'r') as template_js:
            self.setup['js_template'] = template_js.read()
        logger.debug('Load canary template from file: "{file}".'.format(file=canary_template_path))
        with open(canary_template_path, 'r') as template_html:
            self.setup['canary_template'] = template_html.read()

        # Check if hljs feature need to be enabled, based on theme configuration
        if ('highlightjs' in config['theme']._vars
                and config['theme']._vars['highlightjs']    # noqa: W503
                    and self.config['hljs'] is not False):  # noqa: W503, E127
            logger.debug('"highlightjs" value detected on theme config, enable rendering after decryption.')
            self.config['hljs'] = config['theme']._vars['highlightjs']
        elif self.config['hljs']:
            logger.debug('"highlightjs" feature enabled, enable rendering after decryption.')
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
        elif self.config['mermaid2']:
            logger.debug('"mermaid2" feature enabled, enable rendering after decryption.')
        else:
            logger.info('"mermaid2" feature is disabled in your plugin configuration.')
            self.config['mermaid2'] = False
        # Warn about deprecated features on Version 3.0.0
        deprecated_options_detected = False
        if self.config.get('default_expire_delay'):
            logger.warning('DEPRECATED: Option "default_expire_delay" is no longer supported. Can be removed.')
            deprecated_options_detected = True
        if self.config.get('ignore_missing_secret'):
            logger.warning('DEPRECATED: Option "ignore_missing_secret" is no longer supported. Can be removed.')
            deprecated_options_detected = True
        if deprecated_options_detected:
            logger.warning('DEPRECATED: Features marked as deprecated will be remove in next minor version !')
        if self.config.get('use_secret'):
            logger.error('DEPRECATED: Feature "use_secret" is no longer supported. Please use !ENV at password_inventory instead.')
            os._exit(1)                                 # prevent build without password to avoid leak0

        # Enable experimental code .. :popcorn:
        if self.config['search_index'] == 'dynamically':
            logger.info("EXPERIMENTAL search index encryption enabled.")

        # set default classes in html template
        if self.setup['theme'] == 'material':
            if not self.config['form_class']:
                self.config['form_class'] = 'md-content__inner md-typeset'
            if not self.config['input_class']:
                self.config['input_class'] = 'md-input'
            if not self.config['button_class']:
                self.config['button_class'] = 'md-button md-button--primary'

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


        if self.config['kdf_pow'] == -1:
            if self.config['webcrypto']:
                self.setup['kdf_iterations'] = pow(10,5) # depending on size of password inventory 6-7 might be suitable
            else:
                self.setup['kdf_iterations'] = pow(10,4)
        else:
            self.setup['kdf_iterations'] = pow(10,self.config['kdf_pow'])

        # mkdocs-static-i18n v1.x runs this plugin multiple times
        if 'min_enttropy_spied_on' not in self.setup:self.setup['min_enttropy_spied_on'] = 0
        if 'min_enttropy_secret' not in self.setup:self.setup['min_enttropy_secret'] = 0

        if 'locations' not in self.setup: self.setup['locations'] = {}
        if 'password_keys' not in self.setup: self.setup['password_keys'] = {}
        if 'obfuscate_keys' not in self.setup: self.setup['obfuscate_keys'] = {}
        if 'level_keys' not in self.setup: self.setup['level_keys'] = {}

        if 'keystore_id' not in self.setup: self.setup['keystore_id'] = 0
        if 'keystore' not in self.setup: self.setup['keystore'] = {}
        if 'keystore_password' not in self.setup: self.setup['keystore_password'] = {}
        if 'keystore_userpass' not in self.setup: self.setup['keystore_userpass'] = {}
        if 'keystore_obfuscate' not in self.setup: self.setup['keystore_obfuscate'] = {}

        # rebuild kdf keys only if not in cache
        if 'cache_file' not in self.setup and self.config['cache_file']:
            self.setup['cache_file'] = self.setup['config_path'].joinpath(self.config['cache_file'])
            self.setup['cache_file'].parents[0].mkdir(parents=True, exist_ok=True)
            if self.setup['cache_file'].exists():
                with open(self.setup['cache_file'], 'r') as stream:
                    self.setup['cache'] = yaml.safe_load(stream)
                    if not self.setup['cache']: # if file was empty
                        del self.setup['cache']

        if 'cache' not in self.setup or self.setup['cache']['kdf_iterations'] != self.setup['kdf_iterations']:
            self.setup['cache'] = {}
            self.setup['cache']['userpass'] = {}
            self.setup['cache']['password'] = {}
            self.setup['cache']['obfuscate'] = {}
            self.setup['cache']['kdf_iterations'] = self.setup['kdf_iterations']
            self.setup['keystore_password'] = {}
            self.setup['keystore_userpass'] = {}
            self.setup['keystore_obfuscate'] = {}

        if 'sharelinks' not in self.setup and self.config['sharelinks']:
            self.setup['sharelinks_output'] = self.setup['config_path'].joinpath(self.config['sharelinks_output'])
            self.setup['sharelinks_output'].parents[0].mkdir(parents=True, exist_ok=True)
            self.setup['sharelinks'] = {}

        if 'password_inventory' not in self.setup:
            if self.config['password_file']:
                if self.config['password_inventory']:
                    logger.error("Please define either 'password_file' or 'password_inventory' in mkdocs.yml and not both.")
                    os._exit(1)
                password_file = self.setup['config_path'].joinpath(self.config['password_file'])
                with open(password_file, 'r') as stream:
                    self.setup['password_inventory'] = yaml_load(stream)
            elif self.config['password_inventory']:
                self.setup['password_inventory'] = self.config['password_inventory']
            else:
                self.setup['password_inventory'] = {}

            if self.setup['password_inventory']:

                for level in self.setup['password_inventory'].keys():
                    new_entry = {}
                    self.setup['keystore_id'] += 1
                    new_entry['id'] = quote(self.config['remember_prefix'] + str(self.setup['keystore_id']), safe='~()*!\'')
                    if self.config['insecure_test']:
                        new_entry['key'] = SHA256.new(level.encode()).digest() # sha256 sum of level
                    else:
                        new_entry['key'] = get_random_bytes(32)

                    credentials = self.setup['password_inventory'][level]
                    if isinstance(credentials, list):
                        for password in credentials:
                            if isinstance(password, dict):
                                logger.error("Configuration error in yaml syntax of 'password_inventory': expected string at level '{level}', but found dict!".format(level=level))
                                os._exit(1)
                            if password:
                                self.__add_to_keystore__((KS_PASSWORD,password), new_entry['key'], new_entry['id'])
                            else:
                                logger.error("Empty password found for level '{level}'!".format(level=level))
                                os._exit(1)
                    elif isinstance(credentials, dict):
                        for user in credentials:
                            new_entry['uname'] = user
                            if credentials[user]:
                                self.__add_to_keystore__((user,credentials[user]), new_entry['key'], new_entry['id'])
                            else:
                                logger.error("Empty password found for level '{level}' and user '{user}'!".format(level=level,user=user))
                                os._exit(1)
                    else:
                        if credentials:
                            self.__add_to_keystore__((KS_PASSWORD,credentials), new_entry['key'], new_entry['id'])
                        else:
                            logger.error("Empty password found for level '{level}'!".format(level=level))
                            os._exit(1)
                    self.setup['level_keys'][level] = new_entry

        if 'additional_storage' not in self.setup:
            if self.config['additional_storage_file']:
                storage_file = self.setup['config_path'].joinpath(self.config['additional_storage_file'])
                with open(storage_file, 'r') as stream:
                    self.setup['additional_storage'] = yaml_load(stream)
                
                #init empty if missing
                if 'userpass' not in self.setup['additional_storage']:
                    self.setup['additional_storage']['userpass'] = {}
                if 'password' not in self.setup['additional_storage']:
                    self.setup['additional_storage']['password'] = {}
                
                for entry in self.setup['keystore'].copy():
                    if entry[0] == KS_PASSWORD:
                        if entry[1] in self.setup['additional_storage']['password']:
                            for var in self.setup['additional_storage']['password'][entry[1]]:
                                value = self.setup['additional_storage']['password'][entry[1]][var]
                                self.__vars_to_keystore__(entry, var, value)
                    else:
                        if entry[0] in self.setup['additional_storage']['userpass']:
                            for var in self.setup['additional_storage']['userpass'][entry[0]]:
                                value = self.setup['additional_storage']['userpass'][entry[0]][var]
                                self.__vars_to_keystore__(entry, var, value)

        if self.config['sign_files'] and 'sign_key' not in self.setup:
            sign_key_path = self.setup['config_path'].joinpath(self.config['sign_key'])
            sign_key_path.parents[0].mkdir(parents=True, exist_ok=True)
            if not sign_key_path.exists():
                logger.info('Generating signing key and saving to "{file}".'.format(file=str(self.config['sign_key'])))
                key = ECC.generate(curve='Ed25519')
                self.setup['sign_key'] = key
                with open(sign_key_path,'wt') as f:
                    f.write(key.export_key(format='PEM'))
            else:
                logger.info('Reading signing key from "{file}".'.format(file=str(self.config['sign_key'])))
                with open(sign_key_path,'rt') as f:
                    key = ECC.import_key(f.read())
                    self.setup['sign_key'] = key
            self.setup['files_to_sign'] = []

        if self.config['insecure_test']:
            logger.warning('---------------------------------------------------------------------------------')
            logger.warning('INSECURE test build active. DON\'T upload the site anywhere else than "localhost".')
            logger.warning('---------------------------------------------------------------------------------')

        if self.config['esm']:
            self.setup['js_libraries'] = CRYPTO_ES_LIBRARIES
        else:
            self.setup['js_libraries'] = CRYPTO_JS_LIBRARIES

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
                if self.setup['theme'] == 'material':
                    logger.warning("To enable EXPERIMENTAL search index decryption mkdocs-material needs to be customized (patched)!")
                else:
                    # Overwrite search/*.js files from templates/search with encryptcontent contrib search assets
                    for dir in config['theme'].dirs.copy():
                        if re.compile(r".*[/\\]contrib[/\\]search[/\\]templates$").match(dir):
                            config['theme'].dirs.remove(dir)
                            path = str(PLUGIN_DIR.joinpath('contrib/templates'))
                            config['theme'].dirs.append(path)
                            if 'search/main.js' not in config['extra_javascript']:
                                config['extra_javascript'].append('search/main.js')
                            break
        except Exception as exp:
            logger.exception(exp)

        # optionally download cryptojs
        if not self.config['webcrypto'] and self.config['selfhost'] and self.config['selfhost_download']:
            logger.info('Downloading cryptojs for self-hosting (if needed)...')
            if self.config['selfhost_dir']:
                dlpath = self.setup['config_path'].joinpath(self.config['selfhost_dir'] + '/assets/javascripts/cryptojs/')
            else:
                dlpath = Path(config.data['docs_dir'] + '/assets/javascripts/cryptojs/')
            dlpath.mkdir(parents=True, exist_ok=True)
            for jsurl in self.setup['js_libraries']:
                dlurl = "https:" + jsurl[0]
                filepath = dlpath.joinpath(jsurl[2])
                self.__download_and_check__(filepath, dlurl, jsurl[1])

    @plugins.event_priority(-200)
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
        # level '_global' will be set as global level
        if '_global' in self.setup['level_keys']:
            encryptcontent['level'] = '_global'

        if 'password' in page.meta.keys():
            # If global_password is set, but you don't want to encrypt content
            page_password = str(page.meta.get('password'))
            encryptcontent['password'] = None if page_password == '' else page_password
            # Delete meta password information before rendering to avoid leak :]
            del page.meta['password']

        if 'use_secret' in page.meta.keys():
            logger.error('DEPRECATED: Feature "use_secret" is no longer supported. Please use !ENV at password_inventory instead.')
            os._exit(1)                                 # prevent build without password to avoid leak0

        if 'obfuscate' in page.meta.keys():
            encryptcontent['obfuscate'] = str(page.meta.get('obfuscate'))
            del page.meta['obfuscate']

        if 'level' in page.meta.keys():
            # If '_global' level is set, but you don't want to encrypt content
            page_level = str(page.meta.get('level'))
            encryptcontent['level'] = None if page_level == '' else page_level
            del page.meta['level']

        if 'inject_id' in page.meta.keys():
            id = page.meta.get('inject_id')
            encryptcontent['inject'] = {}
            encryptcontent['inject'][id] = ['div', 'id']
            del page.meta['inject_id']
        elif self.config['inject']:
            encryptcontent['inject'] = self.config['inject']

        if 'delete_id' in page.meta.keys():
            encryptcontent['delete_id'] = page.meta.get('delete_id')
            del page.meta['delete_id']

        # Custom per-page strings
        if 'encryption_summary' in page.meta.keys():
            encryptcontent['summary'] = str(page.meta.get('encryption_summary'))
            del page.meta['encryption_summary']

        if 'encryption_info_message' in page.meta.keys():
            encryptcontent['encryption_info_message'] = str(page.meta.get('encryption_info_message'))
            del page.meta['encryption_info_message']

        if encryptcontent.get('password'):
            index = encryptcontent['password']
            if index not in self.setup['password_keys']:
                new_entry = {}
                self.setup['keystore_id'] += 1
                new_entry['id'] = quote(self.config['remember_prefix'] + str(self.setup['keystore_id']), safe='~()*!\'')
                if self.config['insecure_test']:
                    new_entry['key'] = SHA256.new(index.encode()).digest() # sha256 sum of password
                else:
                    new_entry['key'] = get_random_bytes(32)
                self.__add_to_keystore__((KS_PASSWORD,index), new_entry['key'], new_entry['id'])
                self.setup['password_keys'][index] = new_entry
            encryptcontent['type'] = 'password'
            encryptcontent['key'] = self.setup['password_keys'][index]['key']
            encryptcontent['id'] = self.setup['password_keys'][index]['id']
            setattr(page, 'encryptcontent', encryptcontent)
        elif encryptcontent.get('level'):
            index = encryptcontent['level']
            if not index in self.setup['level_keys']:
                logger.error('Please define "{level}" in password_inventory or password_file!'.format(level=index))
                os._exit(1)
            encryptcontent['type'] = 'level'
            encryptcontent['key'] = self.setup['level_keys'][index]['key']
            encryptcontent['id'] = self.setup['level_keys'][index]['id']
            setattr(page, 'encryptcontent', encryptcontent)
        elif encryptcontent.get('obfuscate'):
            index = encryptcontent['obfuscate']
            if index not in self.setup['obfuscate_keys']:
                new_entry = {}
                self.setup['keystore_id'] += 1
                new_entry['id'] = quote(self.config['remember_prefix'] + str(self.setup['keystore_id']), safe='~()*!\'')
                if self.config['insecure_test']:
                    new_entry['key'] = SHA256.new(index.encode()).digest() # sha256 sum of password
                else:
                    new_entry['key'] = get_random_bytes(32)
                self.__add_to_keystore__((KS_OBFUSCATE,index), new_entry['key'], new_entry['id'])
                self.setup['obfuscate_keys'][index] = new_entry
            encryptcontent['type'] = 'obfuscate'
            encryptcontent['key'] = self.setup['obfuscate_keys'][index]['key']
            encryptcontent['id'] = self.setup['obfuscate_keys'][index]['id']
            setattr(page, 'encryptcontent', encryptcontent)

        # Gernerate sharelink entry
        if hasattr(page, 'encryptcontent') and 'sharelink' in page.meta.keys():
            if self.config['sharelinks'] and page.meta.get('sharelink'):
                if page.url not in self.setup['sharelinks']:
                    if page.encryptcontent.get('password'):
                        self.setup['sharelinks'][page.url] = ('', page.encryptcontent['password'])
                    elif page.encryptcontent.get('level'):
                        level = page.encryptcontent['level']
                        credentials = self.setup['password_inventory'][level]
                        if isinstance(credentials, dict):
                            self.setup['sharelinks'][page.url] = next(iter( credentials.items() ))
                        elif isinstance(credentials, list):
                            self.setup['sharelinks'][page.url] = ('', credentials[0])
                        else:
                            self.setup['sharelinks'][page.url] = ('', credentials)
                    elif page.encryptcontent.get('obfuscate'):
                        self.setup['sharelinks'][page.url] = ('', page.encryptcontent['obfuscate'])
                    

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
            if not 'inject' in page.encryptcontent:
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

        # Add obfuscate keys to all other keystores
        keystore = self.setup['keystore'].copy() # make a copy()
        for index in keystore:
            if index[0] == KS_OBFUSCATE:
                if index not in self.setup['keystore_obfuscate']:
                    self.setup['keystore_obfuscate'][index] = ';'.join(self.__encrypt_keys_from_keystore__(index))
                    obfuscate_id = list(keystore[index].keys())[0]
                    for index2 in keystore:
                        if index2[0] == KS_OBFUSCATE:
                            pass
                        else:
                            if obfuscate_id not in self.setup['keystore'][index2].keys():
                                self.setup['keystore'][index2][obfuscate_id] = keystore[index][obfuscate_id]

        #find longest keystore
        max_keystore_length = 0
        for index in self.setup['keystore']:
            keystore_length = len(json.dumps(self.setup['keystore'][index]))
            if keystore_length > max_keystore_length:
                max_keystore_length = keystore_length

        # Encrypt all keys to keystore
        # It just encrypts once, but needs to run on every page
        for index in self.setup['keystore']:
            if index[0] == KS_OBFUSCATE:
                pass
            elif index[0] == KS_PASSWORD:
                if index not in self.setup['keystore_password']:
                    self.setup['keystore_password'][index] = ';'.join(self.__encrypt_keys_from_keystore__(index, max_keystore_length))
            else:
                if index not in self.setup['keystore_userpass']:
                    self.setup['keystore_userpass'][index] = ';'.join(self.__encrypt_keys_from_keystore__(index, max_keystore_length))

        if hasattr(page, 'encryptcontent'):

            if 'i18n_page_locale' in context:
                locale = context['i18n_page_locale']
                if locale in self.config['translations']:
                    translations = self.config['translations'][locale]

                    #apply translation if defined
                    if 'title_prefix' in translations and 'title_prefix' not in page.encryptcontent:
                        page.encryptcontent['title_prefix'] = translations['title_prefix']
                    if 'summary' in translations and 'summary' not in page.encryptcontent:
                        page.encryptcontent['summary'] = translations['summary']
                    if 'placeholder' in translations and 'placeholder' not in page.encryptcontent:
                        page.encryptcontent['placeholder'] = translations['placeholder']
                    if 'placeholder_user' in translations and 'placeholder_user' not in page.encryptcontent:
                        page.encryptcontent['placeholder_user'] = translations['placeholder_user']
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
            if 'placeholder_user' not in page.encryptcontent:
                page.encryptcontent['placeholder_user'] = self.config['placeholder_user']
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

            if 'inject' in page.encryptcontent:
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
        if hasattr(page, 'encryptcontent') and 'inject' in page.encryptcontent:
            encrypted_something = {**page.encryptcontent['inject'], **self.config['encrypted_something']}
        else:
            encrypted_something = self.config['encrypted_something']
        
        if (encrypted_something and hasattr(page, 'encryptcontent')
                and len(encrypted_something) > 0):  # noqa: W503
            soup = BeautifulSoup(output_content, 'html.parser')
            for name, tag in encrypted_something.items():
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
                        cipher_bundle = self.__encrypt_text__(merge_item, page.encryptcontent['key'])
                        encrypted_content = ';'.join(cipher_bundle)
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

            if 'inject' in page.encryptcontent:
                name, tag = list(page.encryptcontent['inject'].items())[0]
                injector = soup.new_tag("div")
                something_search = soup.find(tag[0], {tag[1]: name})
                if not something_search:
                    logger.error('Could not find tag to inject!\n{name}: [{tag0}, {tag1}]'.format(tag0=tag[0], tag1=tag[1], name=name))
                    os._exit(1)
                something_search.insert_before(injector)
                injector.append(BeautifulSoup(page.encryptcontent['decrypt_form'], 'html.parser'))
                page.encryptcontent['decrypt_form'] = None

            output_content = str(soup)

        if hasattr(page, 'encryptcontent'):
            location = page.url.lstrip('/')
            self.setup['locations'][location] = (page.encryptcontent['key'], page.encryptcontent['id'])
            delattr(page, 'encryptcontent')

            if self.config['sign_files']:
                new_entry = {}
                new_entry['file'] = Path(config.data["site_dir"]).joinpath(page.file.dest_uri)
                new_entry['url'] = config.data["site_url"] + page.file.url
                self.setup['files_to_sign'].append(new_entry)

        return output_content

    @plugins.event_priority(-200)
    def on_post_build(self, config, **kwargs):
        """
        The post_build event does not alter any variables.
        Use this event to call post-build scripts.

        :param config: global configuration object
        """
        
        Path(config.data["site_dir"] + '/assets/javascripts/').mkdir(parents=True, exist_ok=True)
        decrypt_js_path = Path(config.data["site_dir"]).joinpath('assets/javascripts/decrypt-contents.js')
        with open(decrypt_js_path, "w") as file:
            file.write(self.__generate_decrypt_js__())

        if self.config['sign_files']:
            new_entry = {}
            new_entry['file'] = decrypt_js_path
            new_entry['url'] = config.data["site_url"] + 'assets/javascripts/decrypt-contents.js'
            self.setup['files_to_sign'].append(new_entry)
            if not self.config['webcrypto']:
                for jsurl in self.setup['js_libraries']:
                    new_entry = {}
                    if self.config['selfhost']:
                        new_entry['file'] = Path(config.data["site_dir"]).joinpath('assets/javascripts/cryptojs/' + jsurl[2])
                        new_entry['url'] = config.data["site_url"] + 'assets/javascripts/cryptojs/' + jsurl[2]
                    else:
                        new_entry['file'] =  ""
                        new_entry['url'] = "https:" + jsurl[0]
                    self.setup['files_to_sign'].append(new_entry)

        #modify search_index in the style of mkdocs-exclude-search
        if self.setup['search_plugin_found'] and self.config['search_index'] != 'clear':
            search_index_filename = Path(config.data["site_dir"]).joinpath('search/search_index.json')
            try:
                with open(search_index_filename, "r") as f:
                    search_entries = json.load(f)
            except:
                logger.error('Search index needs modification, but could not read "search_index.json"!')
                os._exit(1)

            for entry in search_entries['docs'].copy(): #iterate through all entries of search_index
                for location in self.setup['locations'].keys():
                    if entry['location'] == location or entry['location'].startswith(location+"#"): #find the ones located at encrypted pages
                        page_key = self.setup['locations'][location][0]
                        page_id = self.setup['locations'][location][1]
                        if self.config['search_index'] == 'encrypted':
                            search_entries['docs'].remove(entry)
                        elif self.config['search_index'] == 'dynamically' and page_key is not None:
                            #encrypt text/title/location
                            text = entry['text']
                            title = entry['title']
                            location = entry['location']
                            code = self.__encrypt_text__(location, page_key)
                            entry['location'] = page_id + ';' + ';'.join(code) # add encryptcontent_id
                            code = self.__encrypt_text__(text, page_key )
                            entry['text'] = ';'.join(code)
                            code = self.__encrypt_text__(title, page_key)
                            entry['title'] = ';'.join(code)
                        break
            try:
                with open(search_index_filename, "w") as f:
                    json.dump(search_entries, f)
            except:
                logger.error('Search index needs modification, but could not write "search_index.json"!')
                os._exit(1)
            logger.info('Modified search_index.')

        if self.setup['min_enttropy_spied_on'] < 100 and self.setup['min_enttropy_spied_on'] > 0:
            logger.warning('mkdocs-encryptcontent-plugin will always be vulnerable to brute-force attacks!'
                           ' Your weakest password only got {spied_on} bits of entropy, if someone watched you while typing'
                           ' (and a maximum of {secret} bits total)!'.format(spied_on = math.ceil(self.setup['min_enttropy_spied_on']), secret = math.ceil(self.setup['min_enttropy_secret']))
                    )

        if 'cache_file' in self.setup:
            with open(self.setup['cache_file'], 'w') as stream:
                stream.write(yaml.dump(self.setup['cache']))

        if self.config['sharelinks']:
            sharelinks = []
            for page in self.setup['sharelinks']:
                username, password = self.setup['sharelinks'][page]
                if self.config['sharelinks_incomplete'] and ':' in password:
                    password = password.rsplit(':',1)[0] + ":" # don't add the remaining part after the last ":" to the sharelink
                sharelinks.append(config.data["site_url"] + page + '#' + self.__b64url_encode__('!' + username + ':' + password))
            with open(self.setup['sharelinks_output'], 'w') as stream:
                stream.write('\n'.join(sharelinks))

        if self.config['sign_files']:
            signatures = {}
            urls_to_verify = []
            for file in self.setup['files_to_sign']:
                signatures[file['url']] = self.__sign_file__(file['file'], file['url'], self.setup['sign_key'])
                urls_to_verify.append(file['url'])
            if signatures:
                sign_file_path = Path(config.data["site_dir"]).joinpath(self.config['sign_files'])
                sign_file_path.parents[0].mkdir(parents=True, exist_ok=True)
                with open(sign_file_path, "w") as file:
                    file.write(json.dumps(signatures))

            canary_file = self.setup['config_path'].joinpath('canary.py')
            canary_py = Template(self.setup['canary_template']).render({
                'public_key': self.setup['sign_key'].public_key().export_key(format='PEM'),
                'signature_url': config.data["site_url"] + self.config['sign_files'],
                'urls_to_verify': json.dumps(urls_to_verify),
            })
            with open(canary_file, 'w') as file:
                file.write(canary_py)
