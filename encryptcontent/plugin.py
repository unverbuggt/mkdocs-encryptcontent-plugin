
import os
import base64
import hashlib
import logging
from Crypto import Random
from jinja2 import Template
from Crypto.Cipher import AES
from bs4 import BeautifulSoup
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

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
DECRYPT_FORM_TPL_PATH = os.path.join(PLUGIN_DIR, 'decrypt-form.tpl.html')

with open(DECRYPT_FORM_TPL_PATH, 'r') as template:
    DECRYPT_FORM_TPL = template.read()

settings = {
    'title_prefix': '[Protected] ',
    'summary': 'This content is protected with AES encryption. ',
    'placeholder': 'Provide password and press ENTER',
    'password_button_text': 'Decrypt',
    'decryption_failure_message': 'Invalid password.',
    'encryption_info_message': 'Contact your administrator for access to this page.'
}

logger = logging.getLogger("mkdocs.plugins.encryptcontent")

class encryptContentPlugin(BasePlugin):
    """ Plugin that encrypt markdown content with AES and inject decrypt form. """

    config_scheme = (
        ('title_prefix', config_options.Type(string_types, default=str(settings['title_prefix']))),
        ('summary', config_options.Type(string_types, default=str(settings['summary']))),
        ('placeholder', config_options.Type(string_types, default=str(settings['placeholder']))),
        ('decryption_failure_message', config_options.Type(string_types, default=str(settings['decryption_failure_message']))),
        ('encryption_info_message', config_options.Type(string_types, default=str(settings['encryption_info_message']))),
        ('password_button_text', config_options.Type(string_types, default=str(settings['password_button_text']))),
        ('global_password', config_options.Type(string_types, default=None)),
        ('password', config_options.Type(string_types, default=None)),
        ('arithmatex', config_options.Type(bool, default=False)),
        ('hljs', config_options.Type(bool, default=False)),
        ('remember_password', config_options.Type(bool, default=False)),
        ('disable_cookie_protection', config_options.Type(bool, default=False)),
        ('tag_encrypted_page', config_options.Type(bool, default=True)),
        ('password_button', config_options.Type(bool, default=False)),
        ('encrypted_something', config_options.Type(dict, default={})),
        ('decrypt_search', config_options.Type(bool, default=False)),
        ('reload_scripts', config_options.Type(list, default=[])),
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
        ciphertext_bundle = self.__encrypt_text_aes__(content, self.config['password'])
        decrypt_form = Template(DECRYPT_FORM_TPL).render({
            # custom message and template rendering
            'summary': self.config['summary'],
            'placeholder': self.config['placeholder'],
            'password_button': self.config['password_button'],
            'password_button_text': self.config['password_button_text'],
            'decryption_failure_message': self.config['decryption_failure_message'],
            'encryption_info_message': self.config['encryption_info_message'],
            # this benign decoding is necessary before writing to the template,
            # otherwise the output string will be wrapped with b''
            'ciphertext_bundle': b';'.join(ciphertext_bundle).decode('ascii'),
            'js_libraries': JS_LIBRARIES,
            # enable / disable features
            'arithmatex': self.config['arithmatex'],
            'hljs': self.config['hljs'],
            'remember_password': self.config['remember_password'],
            'disable_cookie_protection': self.config['disable_cookie_protection'],
            'encrypted_something': self.config['encrypted_something'],
            'reload_scripts': self.config['reload_scripts'],
        })
        return decrypt_form

    # MKDOCS Events builds

    def on_config(self, config, **kwargs):
        """
        The config event is the first event called on build and is run immediately after
        the user configuration is loaded and validated. Any alterations to the config should be made here.
        Configure plugin self.config from configuration file (mkdocs.yml)

        :param config: global configuration object (mkdocs.yml)
        :return: global configuration object modified to include templates files
        """
        # Check if global password is set on plugin configuration
        self.config['password'] = self.config['global_password']
        # Check if hljs feature need to be enabled, based on theme configuration
        if 'highlightjs' in config['theme']._vars and config['theme']._vars['highlightjs']:
            logger.debug('"highlightjs" value detected on theme config, enable rendering after decryption.')
            self.config['hljs'] = config['theme']._vars['highlightjs']
        # Check if pymdownx.arithmatex feature need to be enabled, based on markdown_extensions configuration
        if 'pymdownx.arithmatex' in config['markdown_extensions']:
            logger.debug('"arithmatex" value detected on extensions config, enable rendering after decryption.')
            self.config['arithmatex'] = True

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
            page_password = page.meta.get('password')
            self.config['password'] = None if page_password == '' else page_password
            # Delete meta password information before rendering to avoid leak :]
            del page.meta['password']
        return markdown

    def on_page_content(self, html, page, config, **kwargs):
        """
        The page_content event is called after the Markdown text is rendered to HTML 
        (but before being passed to a template) and can be used to alter the HTML body of the page.
        Generate encrypt content with AES and add form to decrypt this content with JS.
        Keep the generated value in a temporary attribute for the search work on clear version of content.

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
            setattr(page, 'password', self.config['password'])
            # Keep encrypted html as temporary variable on page cause we need clear html for search plugin
            if self.config['decrypt_search']:
                # Keep encrypted html as temporary variable on page ... :(
                setattr(page, 'html_encrypted', self.__encrypt_content__(html))
            else:
                # Overwrite html with encrypted html, cause search it's encrypted too
                # Process encryption here, speed up mkdocs-search bultin plugin
                html = self.__encrypt_content__(html)
        return html

    def on_page_context(self, context, page, config, **kwargs):
        """
        The page_context event is called after the context for a page is created and
        can be used to alter the context for that specific page only.

        :param context: dict of template context variables
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :param nav: global navigation object
        :return: dict of template context variables
        """
        if self.config['decrypt_search'] and page.content and hasattr(page, 'html_encrypted'):
            page.content = page.html_encrypted
            delattr(page, 'html_encrypted')
        return context

    def on_post_page(self, output_content, page, config, **kwargs):
        """
        The post_page event is called after the template is rendered,
        but before it is written to disc and can be used to alter the output of the page.
        If an empty string is returned, the page is skipped and nothing is written to disc.
        Finds other parts of HTML that need to be encrypted and 
        replaces the content with a protected version 

        :param output_content: output of rendered template as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :return: output of rendered template as string
        """
        # Limit this process only if encrypted_something feature is enable *(speedup)*
        if self.config['encrypted_something'] and hasattr(page, 'encrypted') \
            and len(self.config['encrypted_something']) > 0:
            soup = BeautifulSoup(output_content, 'html.parser')
            for name, tag in self.config['encrypted_something'].items():
                #logger.debug({'name': name, 'html tag': tag[0], 'type': tag[1]})
                something_search = soup.findAll(tag[0], { tag[1]: name })
                if something_search is not None and len(something_search) > 0:
                    # Loop for multi child tags on target element
                    for item in something_search:
                        # Remove '\n', ' ' useless content generated by bs4 parsing...
                        item.contents = [content for content in item.contents if not content in ['\n', ' ']]
                        # Merge the content in case there are several elements
                        if len(item.contents) > 1:
                            merge_item = ''.join([str(s) for s in item.contents])
                        elif len(item.contents) == 1:
                            merge_item = item.contents[0]
                        else:
                            merge_item = ""
                        # Encrypt child items on target tags with page password
                        cipher_bundle = self.__encrypt_text_aes__(merge_item, page.password)
                        encrypted_content = b';'.join(cipher_bundle).decode('ascii')
                        # Replace initial content with encrypted one
                        bs4_encrypted_content = BeautifulSoup(encrypted_content, 'html.parser')
                        item.contents = [bs4_encrypted_content]
                        if item.has_attr('style'):
                            if isinstance(item['style'], list):
                                item['style'].append("display:none")
                            else:
                                item['style'] = item['class'] + "display:none"
                        else:
                            item['style'] = "display:none"
            output_content = str(soup)
        return output_content

    def on_post_build(self, config):
        """
        The post_build event does not alter any variables.
        Use this event to call post-build scripts.

      :param config: global configuration object
        """


