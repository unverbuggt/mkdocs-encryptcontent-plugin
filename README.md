# mkdocs-encryptcontent-plugin

*This plugin allows you to have password protected articles and pages in MKdocs. The content is encrypted with AES-256 in Python using PyCrypto, and decrypted in the browser with Crypto-JS. It has been tested in Python 2.7 and Python 3.5.*

An mkdocs version of the plugin [Encrypt content](https://github.com/mindcruzer/pelican-encrypt-content) for Pelican.

**usecase**

```
I want to be able to protect my articles with password. And I would like this protection to be as granular as possible.
It is possible to define a password to protect each article independently or a global password to encrypt all of them.
If a global password exists, all articles and pages except the homepage are encrypted with this password.
If a password is defined in an article or a page, it is always used even if a global password exists.
If a password is defined as an empty character string, the page is not encrypted.
```

## Installation

Install the package with pip:

```bash
pip install -r requirements.txt
pip install mkdocs-encryptcontent-plugin
```

Install the package from source with pip:

```bash
cd mkdocs-encryptcontent-plugin/
python3 setup.py sdist bdist_wheel
pip3 install dist/mkdocs_encryptcontent_plugin-0.0.1-py3-none-any.whl
```

Enable the plugin in your `mkdocs.yml`:

```yaml
plugins:
    - search
    - encryptcontent: {}
```

You are then able to use the meta tag `password: secret_password` in your markdown files to protect them.

> **Note:** If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.


### Using global password protection

Add `global_password: your_password` in plugin config variable, to protect by default your articles with this password

```yaml
plugins:
    - search
    - encryptcontent:
        global_password: 'your_password'
```

If a password is defined in an article, it will ALWAYS overwrite the global password. 

> **NOTE** Keep in mind that if the `password:` tag exists without value in an article, it will not be protected !


## Features

### HighlightJS support

If your theme use HighlightJS module to improve color, and `highlightjs: true` is set in your `mkdocs.yml`, this plugin enable this part of the jinja template to force reload heiglighting in decrypted content.

```jinja
{% if hljs %}
document.getElementById("mkdocs-decrypted-content").querySelectorAll('pre code').forEach((block) => {
    hljs.highlightBlock(block);
});
{% endif %}
```


## Testing

```bash
virtualenv venv -p python3.5
source venv/bin/activate
python setup.py test
pytest test
```

## Contributing

From reporting a bug to submitting a pull request: every contribution is appreciated and welcome.
Report bugs, ask questions and request features using [Github issues][github-issues].
If you want to contribute to the code of this project, please read the [Contribution Guidelines][contributing].

[mkdocs-plugins]: http://www.mkdocs.org/user-guide/plugins/
[github-issues]: https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues
[contributing]: CONTRIBUTING.md

### Contributors

- [](https://github.com/)
