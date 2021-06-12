
import os
import re
import mkdocs
import base64
import hashlib
import logging
from Crypto import Random
from jinja2 import Template
from Crypto.Cipher import AES
from bs4 import BeautifulSoup
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
    'decryption_failure_message': 'Invalid password.',
    'encryption_info_message': 'Contact your administrator for access to this page.'
}

logger = logging.getLogger("mkdocs.plugins.encryptcontent")

class encryptContentPlugin(BasePlugin):
    """ Plugin that encrypt markdown content with AES and inject decrypt form. """

    config_scheme = (
        ('title_prefix', mkdocs.config.config_options.Type(string_types, default=str(settings['title_prefix']))),
        ('summary', mkdocs.config.config_options.Type(string_types, default=str(settings['summary']))),
        ('placeholder', mkdocs.config.config_options.Type(string_types, default=str(settings['placeholder']))),
        ('decryption_failure_message', mkdocs.config.config_options.Type(string_types, default=str(settings['decryption_failure_message']))),
        ('encryption_info_message', mkdocs.config.config_options.Type(string_types, default=str(settings['encryption_info_message']))),
        ('global_password', mkdocs.config.config_options.Type(string_types, default=None)),
        ('password', mkdocs.config.config_options.Type(string_types, default=None)),
        ('arithmatex', mkdocs.config.config_options.Type(bool, default=False)),
        ('hljs', mkdocs.config.config_options.Type(bool, default=False)),
        ('remember_password', mkdocs.config.config_options.Type(bool, default=False)),
        ('disable_cookie_protection', mkdocs.config.config_options.Type(bool, default=False)),
        ('tag_encrypted_page', mkdocs.config.config_options.Type(bool, default=False)),
        ('password_button', mkdocs.config.config_options.Type(bool, default=False)),
        ('password_button_text', mkdocs.config.config_options.Type(string_types, default=str(settings['password_button_text']))),
        ('encrypted_something', mkdocs.config.config_options.Type(dict, default={})),
        ('decrypt_search', mkdocs.config.config_options.Type(bool, default=False)),
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
            'encryption_info_message': self.encryption_info_message,
            # this benign decoding is necessary before writing to the template, 
            # otherwise the output string will be wrapped with b''
            'ciphertext_bundle': b';'.join(ciphertext_bundle).decode('ascii'),
            'js_libraries': JS_LIBRARIES,
            # enable / disable features
            'arithmatex': self.arithmatex,
            'hljs': self.hljs,
            'remember_password': self.remember_password,
            'disable_cookie_protection': self.disable_cookie_protection,
            'encrypted_something': self.encrypted_something,
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
        # Check if encryption_info_message description is set on plugin configuration to overwrite
        encryption_info_message = plugin_config.get('encryption_info_message')
        setattr(self, 'encryption_info_message', encryption_info_message)
        # Check if hljs feature need to be enabled, based on theme configuration
        setattr(self, 'hljs', None)
        if 'highlightjs' in config['theme']._vars:
            highlightjs = config['theme']._vars['highlightjs']       
            if highlightjs:
                setattr(self, 'hljs', highlightjs)
        # Check if pymdownx.arithmatex feature need to be enabled, based on markdown_extensions configuration
        setattr(self, 'arithmatex', None)
        if 'pymdownx.arithmatex' in config['markdown_extensions']:
            setattr(self, 'arithmatex', True)
        # Check if tag_encrypted_page feature is enable: add an extra attribute `encrypted` is add on page object
        setattr(self, 'tag_encrypted_page', False)
        if 'tag_encrypted_page' in plugin_config.keys():
            tag_encrypted_page = self.config.get('tag_encrypted_page')
            setattr(self, 'tag_encrypted_page', tag_encrypted_page)
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
        # Check if encrypted_something feature is enable: encrypt each other html tags targets
        setattr(self, 'encrypted_something', {})
        if 'encrypted_something' in plugin_config.keys():
            encrypted_something = self.config.get('encrypted_something')
            setattr(self, 'encrypted_something', encrypted_something)
        # Check if decrypt_search is enable: generate search_index.json on clear text (Data leak)
        setattr(self, 'decrypt_search', False)
        if 'decrypt_search' in plugin_config.keys():
            decrypt_search = self.config.get('decrypt_search')
            setattr(self, 'decrypt_search', decrypt_search)            

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
            # If global_password is set, but you don't want to encrypt content
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
        # Encrypt content with password
        if self.password is not None:
            # Add prefix 'text' on title if page is encrypted
            if self.title_prefix:
                page.title = str(self.title_prefix) + str(page.title)
            if self.tag_encrypted_page:
                # Set attribute on page to identify encrypted page on template rendering
                setattr(page, 'encrypted', True)
            if self.decrypt_search:
                # Keep encrypted html as temporary variable on page ... :(
                setattr(page, 'html_encrypted', self.__encrypt_content__(html))
            else:
                # Overwrite html with encrypted html, cause search it's encrypted too
                # Process encryption here, speed up mkdocs-search bultin plugin
                html = self.__encrypt_content__(html)
            if self.encrypted_something:
                # Set attributes on page to retrieve password on POST context
                setattr(page, 'password', self.password)
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
        if self.decrypt_search and page.content and hasattr(page, 'html_encrypted'):
            page.content = page.html_encrypted
            delattr(page, 'html_encrypted')
        return context

    def on_post_page(self, output_content, page, config, **kwargs):
        """
        The post_page event is called after the template is rendered,
        but before it is written to disc and can be used to alter the output of the page.
        If an empty string is returned, the page is skipped and nothing is written to disc.

        :param output_content: output of rendered template as string
        :param page: mkdocs.nav.Page instance
        :param config: global configuration object
        :return: output of rendered template as string
        """
        # Limit this process only if encrypted_something feature is enable *(speedup)*
        if self.encrypted_something and hasattr(page, 'encrypted') and len(self.encrypted_something) > 0:
            soup = BeautifulSoup(output_content, 'html.parser')
            for name, tag in self.encrypted_something.items():
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


