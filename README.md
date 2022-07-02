# mkdocs-encryptcontent-plugin

[![PyPI Version][pypi-v-image]][pypi-v-link]
[![PyPI downloads](https://img.shields.io/pypi/dm/mkdocs-encryptcontent-plugin.svg)](https://pypi.org/project/mkdocs-encryptcontent-plugin)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

This plugin allows you to have password protected articles and pages in MKdocs.

The content is encrypted with AES-256 in Python using PyCryptodome, and decrypted in the browser with Crypto-JS.

*It has been tested in Python Python 3.5+*

**Usecase**

> I want to be able to protect the content of the page with a password.
>
> Define a password to protect each page independently or a global password to protect them all.
>
> If a global password exists, all articles and pages are protected with this password.
>
> If a password is defined in an article or a page, it is always used even if there is a global password.
>
> If a password is defined as an empty character string, the content is not protected.

![encryptcontent_demo](https://user-images.githubusercontent.com/12155947/177001700-f0920d4b-0c41-4d11-8164-9f63d29d8a6a.gif)


# Table of Contents

  * [Installation](#installation)
  * [Usage](#usage)
    * [Global password protection](#global-password-protection)
    * [Secret from environment](#secret-from-environment)
    * [Customization](#extra-vars-customization)
  * [Features](#features)
    * [HighlightJS support](#highlightjs-support) *(default)*
    * [Arithmatex support](#arithmatex-support) *(default)*
    * [Mermaid2 support](#mermaid-support) *(default)*
    * [Tag encrypted page](#tag-encrypted-page) *(default)*
    * [Rebember password](#rebember-password)
    * [Encrypt something](#encrypt-something)
    * [Search index encryption](#search-index-encryption)
    * [Add button](#add-button)
    * [Reload scripts](#reload-scripts)
  * [Contributing](#contributing)


# Installation

Install the package with pip:

```bash
pip install mkdocs-encryptcontent-plugin
```

Install the package from source with pip:

```bash
cd mkdocs-encryptcontent-plugin/
python3 setup.py sdist bdist_wheel
pip3 install dist/mkdocs_encryptcontent_plugin-2.2.1-py3-none-any.whl
```

Enable the plugin in your `mkdocs.yml`:

```yaml
plugins:
    - search: {}
    - encryptcontent: {}
```
> **NOTE:** If you have no `plugins` entry in your configuration file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.


# Usage

Add an meta tag `password: secret_password` in your markdown files to protect them.


### Global password protection

Add `global_password: your_password` in plugin configuration variable, to protect by default your articles with this password

```yaml
plugins:
    - encryptcontent:
        global_password: 'your_password'
```

If a password is defined in an article, it will **ALWAYS** overwrite the global password. 

> **NOTE** Keep in mind that if the `password:` tag exists without value in an article, it will **not be protected** !


### Secret from environment

Instead of specifying a password in the mkdocs.yml file, you can use an environment variable to load your secret. 

This process is in two steps:

1. First, you need to make an environment variable with your global password accessible at runtime (via any CI/CD pipeline or by setting it yourself in your environment).


2. Then in the mkdocs.yml file, instead of specifying a global password, just set the `use_secret` field with your environment variable name, e.g. in case my secret is stored in the `ENCRYPTCONTENT_PASSWORD` variable:

``` yaml
plugins:
    - encryptcontent:
        use_secret: 'ENCRYPTCONTENT_PASSWORD'
```

> **NOTE** Keep in mind that if the `use_secret:` configuration is set, it will always be used even if you have also set a global password with the `global_password` variable.


### Extra vars customization

Optionally you can use some extra variables in plugin configuration to customize default messages.

```yaml
plugins:
    - encryptcontent:
        title_prefix: '[LOCK]'
        summary: 'another informational message to encrypted content'
        placeholder: 'another password placeholder'
        decryption_failure_message: 'another informational message when decryption fail'
        encryption_info_message: 'another information message when you dont have acess !'
```

Default prefix title is `[Protected]`.

Default summary message is `This content is protected with AES encryption.`.

Default password palceholder is `Provide password and press ENTER`.

Default decryption failure message is `Invalid password.`.

Defaut encryption information message is `Contact your administrator for access to this page.`.

> **NOTE** Adding a prefix to the title does not change the default navigation path !


# Features

### HighlightJS support

> **Enable by default**

If HighlightJS module is detected in your theme to improve code color rendering, reload renderer after decryption process. If HighlightJS module is not correctly detected, you can force the detection by adding `hljs: True` on the plugin configuration or set `hljs: False` to disable this feature.

When enable the following part of the template is add to force reloading decrypted content.

```jinja
{% if hljs %}
document.getElementById("mkdocs-decrypted-content").querySelectorAll('pre code').forEach((block) => {
    hljs.highlightBlock(block);
});
{% endif %}
```

### Arithmatex support

> **Enable by default**

Related to [issue #12](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/12)

If Arithmatex markdown extension is detected in your markdown extensions to improve math equations rendering, reload renderer after decryption process. If the Arithmatex markdown extension is not correctly detected, you can force the detection by adding `arithmatex: True` on the plugin configuration or set `arithmatex: False` to disable this feature.
 
When enable, the following part of the template is add to force math equations rendering on decrypted content.

```jinja
{% if arithmatex %}
MathJax.typesetPromise()
{% endif %}
```

> **NOTE** It has been tested in Arithmatex `generic` mode only. 

### Mermaid2 support

> **Enable by default**

Related to [issue #22](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/22)

If mermaid2 plugin is detected in your configuration to generate graph from text, reload renderer after decryption process. If the Mermaid2 plugin is not correctly detected, you can force the detection by adding `mermaid2: True` on the plugin configuration or set `mermaid2: False` to disable this feature.
 
When enable, the following part of the template is add to force graph rendering on decrypted content.

```jinja
{% if mermaid2 %}
mermaid.contentLoaded();
{% endif %}
```

> **NOTE** It has been tested with Mermaid2 mkdocs plugin only.

### Tag encrypted page

> **Enable by default**

Related to [issue #7](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/7)

This feature add an additional attribute `encrypted` with value `True` to the mkdocs type `mkdocs.nav.page` object.

You can add `tag_encrypted_page: False` in plugin configuration, to disable tagging of encrypted pages. **BUT** This feature is neccessary for others feature working correctly. If you disable this feature, do no use [Encrypt Somethings](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin#encrypt-something), 

When enable, it becomes possible to use `encrypted` attribute in the jinja template of your theme, as a condition to perform custom modification.

```jinja
{%- for nav_item in nav %}
    {% if nav_item.encrypted %}
        <!-- Do something --> 
    {% endif %}
{%- endfor %}
```

For example, in your theme template, you can use conditional check to add custom class :

```jinja
<a {% if nav_item.encrypted %}class="mkdocs-encrypted-class"{% endif %}href="{{ nav_item.url|url }}">{{ nav_item.title }}</a>
```

### Rebember password

Related to [issue #6](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/6)

> :warning: **This feature is not really secure !** Password are store in clear text inside local storage.
>
> Instead of using this feature, I recommend to use a password manager with its web plugins.
> For example **KeepassXC** allows you, with a simple keyboard shortcut, to detect the password field `mkdocs-content-password` and to fill it automatically in a much more secure way.

If you do not have password manager, you can set `remember_password: True` in your `mkdocs.yml` to enable password remember feature.

When enabled, each time you fill password form and press `Enter` a key on local storage is create with your password
as value. When you reload the page, if you already have an 'encryptcontent' key in the local storage of your browser,
the page will be automatically decrypted using the value previously created.

By default, the key is created with a name relative to the page on which it was generated.
This 'relative' key will always be used as first attempt to decrypt the current page when loading.

If your password is a [global password](#global-password-protection), you can fill in the form field  `mkdocs-content-password`, then use the keyboard shortcut `CTRL + ENTER` instead of the classic `ENTER`. 
The key that will be created with a generic name to making it accessible, by default, on all the pages of your site.

The form of decryption remains visible as long as the content has not been successfully decrypted, which allows in case of error to retry. 
All keys created with this feature on localstorage have an default expire time daly set to 24 hours, just cause ...

However *(optionally)*, its possible to change the default expire time by setting options `default_expire_dalay: <number>` in your `mkdocs.yml`. Your configuration should look like this when you enabled this feature :
```yaml
plugins:
    - encryptcontent:
        remember_password: True
        default_expire_dalay: 24   # <-- Default expire delay in hours (optional)
```

> **NOTE** The expired elements of the localStorage are only deleted by the execution of the decrypt-content.js scripts and therefore by the navigation on the site. Secret items can therefore remain visible in local storage after their expiration dates. 

### Encrypt something

Related to [issue #9](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/9)

The [tag encrypted page feature](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin#tag-encrypted-page) **MUST** be enabled (it's default) for this feature to work properly.

Add `encrypted_something: {}` in the plugin configuration variable, to encrypt something else.

The syntax of this new variable **MUST** follow the yaml format of a dictionary. 
Child elements of `encrypted_something` are build with a key `<unique name>` in string format and a list as value. 
The list have to be contructed with the name of an HTML element `<html tag>` as first item and `id` or `class` as the second item.

```yaml
plugins:
    - encryptcontent:
        encrypted_something:
            <uniq name>: [<html tag>, <'class' or 'id'>]
```

The `<unique name>` key identifies the name of a specific element of the page that will be searched by beautifulSoup.
The first value of the `<html tag>` list identifies the type of HTML tag in which the name is present.
The second value of the list, as string `'id'` or `'class'`, specifies the type of the attribute which contains the unique name in the html tag.

Prefer to use an `'id'`, however depending on the template of your theme, it is not always possible to use the id.
So we can use the class attribute to define your unique name inside html tag. 
BeautifulSoup will encrypt all HTML elements discovered with the class.

When the feature is enabled, you can use any methods *(password, button, remember)* to decrypt every elements encrypted on the page.

By default **every child items** are encrypted and the encrypted elements have `style=display:none` to hide their content.

#### How to use it :exploding_head: ?! Examples

Use the `page.encrypted` conditions to add attributes of type id or class in the HTML templates of your theme. 
Each attribute is identified with a unique name and is contained in an html element. 
Then add these elements in the format of a yaml dictionary under the variable `encrypted_something`.

1. For example, encrypt ToC in a theme where ToC is under 'div' element like this :

```jinja
<div class=".." {% if page.encrypted %}id="mkdocs-encrypted-toc"{% endif %}>
    <ul class="..">
        <li class=".."><a href="{{ toc_item.url }}">{{ toc_item.title }}</a></li>
         <li><a href="{{ toc_item.url }}">{{ toc_item.title }}</a></li>
    </ul>
</div>
```

Set your configuration like this : 

```yaml
plugins:
    - encryptcontent:
        encrypted_something:
            mkdocs-encrypted-toc: [div, id]
```

2. Other example, with multiples target. In you Material Theme, you want to encrypt ToC content and Footer.

Materiel generate 2 `<nav>` structure with the same template `toc.html`, so you need to use a `class` instead of an id for this part.
The footer part, is generated by the `footer.html` template in a classic div so an `id` is sufficient

After modification, your template looks like this :
```jinja (toc.html)
<nav class="md-nav md-nav--secondary {% if page.encrypted %}mkdocs-encrypted-toc{% endif %}" aria-label="{{ lang.t('toc.title') }}">
    <label class="md-nav__title" for="__toc"> ... </label>
    <ul class="md-nav__list" data-md-scrollfix> ... </ul>
</nav>
```
```jinja (footer.html)
<footer class="md-footer">
    <div class="md-footer-nav" {% if page.encrypted %}id="mkdocs-encrypted-footer"{% endif %}> ... </div>
    <div class="md-footer-meta md-typeset" {% if page.encrypted %}id="mkdocs-encrypted-footer-meta"{% endif %}>
</footer>
```

Your configuration like this :
```yaml
plugins:
    - encryptcontent:
        encrypted_something:
            mkdocs-encrypted-toc: [nav, class]
            mkdocs-encrypted-footer: [div, id]
            mkdocs-encrypted-footer-meta: [div, id]
```

### Search index encryption

> **Default value is "encrypted"**

Related to [issue #13](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/13)

> :warning: **The configuration mode "clear" of this functionality can cause DATA LEAK**
>
> The unencrypted content of each page is accessible through the search index.
> Not encrypting the search index means completely removing the protection provided by this plugin.
> You have been warned 

This feature allows you to control the behavior of the encryption plugin with the search index. 
Three configuration modes are possible:

 * **clear** : Search index is not encrypted. Search is possible even on protected pages.
 * **dynamically** : Search index is encrypted on build. Search is possible once the pages have been decrypted ones.
 * **encrypted** : Search index is encrypted on build. Search is not possible on all encrypted pages.

You can set `search_index: '<mode_name>'` in your `mkdocs.yml` to change the search index encryption mode. Possible values are `clear`, `dynamically`, `encrypted`. The default mode is "**encrypted**".

```yaml
plugins:
    - encryptcontent:
        search_index: 'dynamically'
```

This functionality overwrite the index creation function of the “search” plug-in provided by mkdocs. The modifications carried out make it possible to encrypt the content of the search index *after* the default plugin has carried out these treatments *(search configuration)*. It is therefore dependent on the default search plugin. 

When the configuration mode is set to "**dynamically**", the [javascripts contribution files](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/tree/experimental/encryptcontent/contrib/templates/search) are used to override the default search plugin files provided by MKdocs. They include a process of decrypting and keeping the search index in a SessionStorage.

> **NOTE** The mode 'dynamically' is currently **not compatible with Material Theme** !

### Add button

Add `password_button: True` in plugin configuration variable, to add button to the right of the password field.

When enable, it allows to decrypt the content just like the classic keypress ENTER. If remember password feature is activated, use button to decrypt generate a 'relative' key on your local storage. You cannot use password button to create global password value.

Optionnally, you can add `password_button_text: 'custom_text_button'` to customize the button text.
 
```yaml
plugins:
    - encryptcontent:
        password_button: True
        password_button_text: 'custom_text_button'
```

### Reload scripts

Related to [issue #14](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/14)

You can set `reload_scripts:` in your `mkdocs.yml` with list of script source, to reload and execute some js lib after decryption process.

```yaml
plugins:
    reload_scripts:
        - "./js/example.js"
```

This feature use the following JQuery function to remove, add and reload javascripts. 

```javascript
var reload_js = function(src) {
    $('script[src="' + src + '"]').remove();
    $('<script>').attr('src', src).appendTo('head');
};
```

# Contributing

From reporting a bug to submitting a pull request: every contribution is appreciated and welcome.

Report bugs, ask questions and request features using [Github issues][github-issues].

If you want to contribute to the code of this project, please read the [Contribution Guidelines][contributing].

[mkdocs-plugins]: https://www.mkdocs.org/dev-guide/plugins/
[github-issues]: https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues
[contributing]: CONTRIBUTING.md

<!-- Badges -->
[pypi-v-image]: https://img.shields.io/pypi/v/mkdocs-encryptcontent-plugin.svg
[pypi-v-link]: https://pypi.org/project/mkdocs-encryptcontent-plugin/