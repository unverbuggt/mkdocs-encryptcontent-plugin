
import os
import mkdocs
import base64
import hashlib
from Crypto import Random
from jinja2 import Template
from Crypto.Cipher import AES
from mkdocs.plugins import BasePlugin

try:
    from mkdocs.utils import string_types
except ImportError:
    string_types = str

JS_LIBRARIES = [
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.0.0/core.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.0.0/enc-base64.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.0.0/cipher-core.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.0.0/pad-nopadding.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.0.0/md5.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/4.0.0/aes.js'
]

PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
DECRYPT_FORM_TPL_PATH = os.path.join(PLUGIN_DIR, 'decrypt-form.tpl.html')

with open(DECRYPT_FORM_TPL_PATH, 'r') as template:
    DECRYPT_FORM_TPL = template.read()

settings = {
    'title_prefix': '[Protected] ',
    'summary': 'This content is protected with AES encryption. ',
    'placeholder': 'Provide password and press ENTER',
    'password_button_text': 'Decrypt',
    'decryption_failure_message': 'Invalid password.'
}


class encryptContentPlugin(BasePlugin):
    """ Plugin that encrypt markdown content with AES and inject decrypt form. """

    config_scheme = (
        ('title_prefix', mkdocs.config.config_options.Type(string_types, default=str(settings['title_prefix']))),
        ('summary', mkdocs.config.config_options.Type(string_types, default=str(settings['summary']))),
        ('placeholder', mkdocs.config.config_options.Type(string_types, default=str(settings['placeholder']))),
        ('decryption_failure_message', mkdocs.config.config_options.Type(string_types, default=str(settings['decryption_failure_message']))),
        ('global_password', mkdocs.config.config_options.Type(string_types, default=None)),
        ('password', mkdocs.config.config_options.Type(string_types, default=None)),
        ('hljs', mkdocs.config.config_options.Type(bool, default=False)),
        ('remember_password', mkdocs.config.config_options.Type(bool, default=False)),
        ('disable_cookie_protection', mkdocs.config.config_options.Type(bool, default=False)),
        ('css_class', mkdocs.config.config_options.Type(string_types, default=None)),
        ('password_button', mkdocs.config.config_options.Type(bool, default=False)),
        ('password_button_text', mkdocs.config.config_options.Type(string_types, default=str(settings['password_button_text']))),
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

    def __encrypt_content__(self, content):
        """ Replaces page or article content with decrypt form. """
        ciphertext_bundle = self.__encrypt_text_aes__(content, self.password)
        decrypt_form = Template(DECRYPT_FORM_TPL).render({
            # custom message and template rendering
            'summary': self.summary,
            'placeholder': self.placeholder,
            'password_button': self.password_button,
            'password_button_text': self.password_button_text,
            'decryption_failure_message': self.decryption_failure_message,
            # this benign decoding is necessary before writing to the template, 
            # otherwise the output string will be wrapped with b''
            'ciphertext_bundle': b';'.join(ciphertext_bundle).decode('ascii'),
            'js_libraries': JS_LIBRARIES,
            # enable / disable features
            'hljs': self.hljs,
            'remember_password': self.remember_password,
            'disable_cookie_protection': self.disable_cookie_protection,
        })
        return decrypt_form

    # MKDOCS Events builds

    def on_pre_build(self, config):
        """
        The pre_build event does not alter any variables. Use this event to call pre-build scripts.
        Here, we load global_password from mkdocs.yml config plugins if global password is define.
        Add some extra vars to customize template
        And check if hljs is needed by theme.

        :param config: global configuration object (mkdocs.yml)
        """
        plugin_config = config['plugins']['encryptcontent'].config
        # Check if global password is set on plugin configuration
        if 'global_password' in config.keys():
            global_password = self.config.get('global_password')
            setattr(self, 'password', global_password)

        # Check if prefix title is set on plugin configuration to overwrite
        title_prefix = plugin_config.get('title_prefix')
        setattr(self, 'title_prefix', title_prefix)
        # Check if summary description is set on plugin configuration to overwrite
        summary = plugin_config.get('summary')
        setattr(self, 'summary', summary)
        # Check if placeholder description is set on plugin configuration to overwrite
        placeholder = plugin_config.get('placeholder')
        setattr(self, 'placeholder', placeholder)
        # Check if decryption_failure_message description is set on plugin configuration to overwrite
        decryption_failure_message = plugin_config.get('decryption_failure_message')
        setattr(self, 'decryption_failure_message', decryption_failure_message)

        # Check if hljs feature need to be enabled, based on theme configuration
        setattr(self, 'hljs', None)
        if 'highlightjs' in config['theme']._vars:
            highlightjs = config['theme']._vars['highlightjs']       
            if highlightjs:
                setattr(self, 'hljs', highlightjs)

        # Check if css_class feature is enable: add a css class to the titles of encrypted pages
        setattr(self, 'css_class', None)
        if 'css_class' in plugin_config.keys():
            css_class = self.config.get('css_class')
            setattr(self, 'css_class', css_class)

        # Check if cookie_password feature is enable: create a cookie for automatic decryption
        setattr(self, 'remember_password', False)
        setattr(self, 'disable_cookie_protection', False)
        if 'remember_password' in plugin_config.keys():
            remember_password = self.config.get('remember_password')
            setattr(self, 'remember_password', remember_password)
            # Check if cookie protection is disable *not good idea*: remove cookie flag 'Secure' & 'sameStie'
            setattr(self, 'disable_cookie_protection', False)
            if 'disable_cookie_protection' in plugin_config.keys():
                disable_cookie_protection = self.config.get('disable_cookie_protection')
                setattr(self, 'disable_cookie_protection', disable_cookie_protection)

        # Check if password_button feature is enable: Add button to trigger decryption process
        if 'password_button' in  plugin_config.keys():
            password_button = plugin_config.get('password_button')
            setattr(self, 'password_button', password_button)
            # Check if password_button_text description is set on plugin configuration to overwrite
            if 'password_button_text' in plugin_config.keys():
                password_button_text = plugin_config.get('password_button_text')
                setattr(self, 'password_button_text', password_button_text)

    def on_page_markdown(self, markdown, page, config, **kwargs):
        """
        The page_markdown event is called after the page's markdown is loaded from file and 
        can be used to alter the Markdown source text. The meta- data has been stripped off 
        and is available as page.meta at this point.
        Here, we load password from meta header *.md pages and override global_password if define.

        :param markdown: Markdown source text of page as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :param site_navigation: global navigation object
        :return: Markdown source text of page as string
        """
        if 'password' in page.meta.keys():
            page_password = page.meta.get('password')
            # If global_password is set, but you dont want to encrypt content
            if page_password == '':
                setattr(self, 'password', None)
            else:
                setattr(self, 'password', page_password)
            # Delete meta password information before rendering to avoid leak :]
            del page.meta['password']
        else:
            page_password = self.config.get('global_password')
            setattr(self, 'password', page_password)
        return markdown

    def on_page_content(self, html, page, config, **kwargs):
        """
        The page_content event is called after the Markdown text is rendered to HTML 
        (but before being passed to a template) and can be used to alter the HTML body of the page.
        Here, we encrypt content with AES and add form to decrypt this content with JS.

        :param html: HTML rendered from Markdown source as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :param site_navigation: global navigation object
        :return: HTML rendered from Markdown source as string encrypt with AES
        """
        # Add prefix 'text' on title if define
        if self.title_prefix:
            page.title = str(self.title_prefix) + str(page.title)
        # Add css class on title if define
        if self.css_class:
            page.title = '<span class="{locked_class}">{title}</span>'.format(
                locked_class=str(self.css_class),
                title=str(page.title)
            )
        # Encrypt content with password
        if self.password is not None:
            html = self.__encrypt_content__(html)
        return html

