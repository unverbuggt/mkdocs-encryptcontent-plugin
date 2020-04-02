
import os
import mkdocs
import base64
import hashlib
from Crypto import Random
from jinja2 import Template
from itertools import chain
from Crypto.Cipher import AES
from mkdocs.plugins import BasePlugin

JS_LIBRARIES = [
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/core.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/enc-base64.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/cipher-core.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/pad-nopadding.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/md5.js',
    '//cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/aes.js'
]

PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
DECRYPT_FORM_TPL_PATH = os.path.join(PLUGIN_DIR, 'decrypt-form.tpl.html')

with open(DECRYPT_FORM_TPL_PATH, 'r') as template:
    DECRYPT_FORM_TPL = template.read()

settings = {
    'title_prefix': '[Protected]',
    'summary': 'This content is protected with AES encryption. '
}


class encryptContentPlugin(BasePlugin):
    """ Plugin that encrypt markdown content with AES and inject decrypt form. """

    config_scheme = (
        ('password', mkdocs.config.config_options.Type(mkdocs.utils.string_types, default=None)),
        ('hljs', mkdocs.config.config_options.Type(bool, default=False)),
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
        hljs = self.hljs
        decrypt_form = Template(DECRYPT_FORM_TPL).render({
            'summary': settings['summary'],
            # this benign decoding is necessary before writing to the template, 
            # otherwise the output string will be wrapped with b''
            'ciphertext_bundle': b';'.join(ciphertext_bundle).decode('ascii'),
            'js_libraries': JS_LIBRARIES,
            'hljs': hljs
        })
        return decrypt_form

    # MKDOCS Events builds

    def on_pre_build(self, config):
        """
        The pre_build event does not alter any variables. Use this event to call pre-build scripts.
        Here, we load global_password from mkdocs.yml config plugins if global password is define.
        And check if hljs is needed by theme.

        :param config: global configuration object
        """
        # Check if global password is set on plugin configuration
        if 'global_password' in config.keys():
            global_password = self.config.get('global_password')
            setattr(self, 'password', global_password)
        # Check if hljs is enable in theme config
        if 'highlightjs' in config['theme']._vars:
            highlightjs = config['theme']._vars['highlightjs']       
            if highlightjs:
                setattr(self, 'hljs', highlightjs)

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
        # Never encrypt home page with global_password
        if not page.is_homepage:
            if self.password is not None:
                html = self.__encrypt_content__(html)
        return html

