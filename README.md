# mkdocs-encryptcontent-plugin

*This plugin allows you to have password protected articles and pages in MKdocs.* 

*The content is encrypted with AES-256 in Python using PyCryptodome, and decrypted in the browser with Crypto-JS.*

*It has been tested in Python 2.7 and Python 3.5+*

An mkdocs version of the plugin [Encrypt content](https://github.com/mindcruzer/pelican-encrypt-content) for Pelican.

**Usecase**

> I want to be able to protect my articles with password. And I would like this protection to be as granular as possible.
>
> It is possible to define a password to protect each article independently or a global password to encrypt all of them.
>
> If a global password exists, all articles and pages except the homepage are encrypted with this password.
>
> If a password is defined in an article or a page, it is always used even if a global password exists.
>
> If a password is defined as an empty character string, the page is not encrypted.


## Installation

Install the package with pip:

```bash
pip install mkdocs-encryptcontent-plugin
```

Install the package from source with pip:

```bash
cd mkdocs-encryptcontent-plugin/
python3 setup.py sdist bdist_wheel
pip3 install dist/mkdocs_encryptcontent_plugin-0.0.4-py3-none-any.whl
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

```yaml
plugins:
    - search
    - encryptcontent:
        global_password: 'your_password'
        title_prefix: '[LOCK]'
        summary: 'another informational message than the default one'
```

Default prefix title is `[Protected]` and default summary message is `This content is protected with AES encryption. `  

> **NOTE** Adding a prefix to the title does not change the default navigation path !


## Features

### HighlightJS support

If your theme use HighlightJS module to improve color, set `highlightjs: true` in your `mkdocs.yml`, to enable color reloading after decryption process.
 
When enable the following part of the template is add to force reloading decrypted content.

```jinja
{% if hljs %}
document.getElementById("mkdocs-decrypted-content").querySelectorAll('pre code').forEach((block) => {
    hljs.highlightBlock(block);
});
{% endif %}
```

### Rebember password

Related to [issue #6](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/6)

> :warning: **This feature is not really secure !** Password are store in clear text inside local cookie without httpOnly flag.
>
> Instead of using this feature, I recommend to use a password manager with its web plugins.
> For example **KeepassXC** allows you, with a simple keyboard shortcut, to detect the password field `mkdocs-content-password` and to fill it automatically in a much more secure way.

If you do not have password manager , you can set `remember_password: True` in your `mkdocs.yml` to enable password remember feature.

When enabled, each time you fill password form and press `Enter` a cookie is create with your password as value. 
When you reload the page, if you already have an 'encryptcontent' cookie in your browser,
the page will be automatically decrypted using the value of the cookie.

By default, the cookie is created with a `path=` relative to the page on which it was generated.
This 'specific' cookie will always be used as first attempt to decrypt the current page when loading.

If your password is a global password, you can fill in the `mkdocs-content-password` field,
then use the keyboard shortcut `CTRL + ENTER` instead of the classic `ENTER`. 
The cookie that will be created with a `path=/` making it accessible, by default, on all the pages of your site.

The form of decryption remains visible as long as the content has not been successfully decrypted,
 which allows in case of error to modify the created cookie.

All cookies created with this feature have the default security options `Secure` and` SameSite=Strict`, just cause ...

However *(optionally)*, its possible to remove these two security options by adding `disable_cookie_protection: True` in your` mkdocs.yml`.

Your configuration should look like this when you enabled this feature :
```yaml
plugins:
    - search
    - encryptcontent:
        remember_password: True
        disable_cookie_protection: True   # <-- Really a bad idea
```

## Contributing

From reporting a bug to submitting a pull request: every contribution is appreciated and welcome.
Report bugs, ask questions and request features using [Github issues][github-issues].
If you want to contribute to the code of this project, please read the [Contribution Guidelines][contributing].

[mkdocs-plugins]: http://www.mkdocs.org/user-guide/plugins/
[github-issues]: https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues
[contributing]: CONTRIBUTING.md

### Contributors

- [anthonyeden](https://github.com/anthonyeden)
