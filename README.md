# mkdocs-encryptcontent-plugin

*This plugin allows you to have password protected articles and pages in MKdocs. The content is encrypted with AES-256 in Python using PyCryptodome, and decrypted in the browser with Crypto-JS. It has been tested in Python 2.7 and Python 3.5+*

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
pip install mkdocs-encryptcontent-plugin
```

Install the package from source with pip:

```bash
cd mkdocs-encryptcontent-plugin/
python3 setup.py sdist bdist_wheel
pip3 install dist/mkdocs_encryptcontent_plugin-0.0.3-py3-none-any.whl
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

### Extra vars customization

Optionally you can add `title_prefix` and `summary` in plugin config variables to customize default messages.

Optionally you can add `remember_password: True` in plugin config variables to enable remember_password feature.

```yaml
plugins:
    - search
    - encryptcontent:
        global_password: 'your_password'
        title_prefix: '[LOCK]'
        summary: 'another informational message than the default one'
        remember_password: true
```

Default prefix title is `[Protected]` and default summary message is `This content is protected with AES encryption. `  

> **NOTE** Adding a prefix to the title does not change the default navigation path !

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

### Rebember password

If like me, your lazy, you can set `remember_password: True` in the configuration variable of this plugin to enable password remember feature.

When enabled, that's allow you to press `CTRL+Enter` key on input password field form, to write your input password on cookie named **encryptcontent_cookie_password**. 
When **encryptcontent_cookie_password** is set and if you just press `Enter` without input on password form, decrypt function use cookie value as default password.
You can update **encryptcontent_cookie_password** value by re-using `CTRL+Enter` after entering your password.

> **NOTE** Disabled by default

## Contributing

From reporting a bug to submitting a pull request: every contribution is appreciated and welcome.
Report bugs, ask questions and request features using [Github issues][github-issues].
If you want to contribute to the code of this project, please read the [Contribution Guidelines][contributing].

[mkdocs-plugins]: http://www.mkdocs.org/user-guide/plugins/
[github-issues]: https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues
[contributing]: CONTRIBUTING.md

### Contributors

- [anthonyeden](https://github.com/anthonyeden)
