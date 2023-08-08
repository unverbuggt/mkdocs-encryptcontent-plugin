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

# Todo for 3.x

* ~~Rework password handling or inventory of some sort~~
* ~~Rework crypto (PBKDF2 + AES256)~~
* ~~Save the generated random keys instead of passwords to session( or local) storage~~
* ~~Sign generated generated and javascript files used in encrypted pages to make it more tamper proof~~
* ~~Add check for latin1 encoding in passwords, as it pycryptodome's implementation of PBKDF2 requires it~~
* ~~find an equivalent way to define multiple passwords in the password inventory as global password~~
* ~~make it possible to define passwords in external yaml file(s)~~
* ~~decrypt all possible keys by one login (replace path fallback)~~
* optional server side keystore (allows throtteling)
* optional replace crypto-js by webcrypto functions
* localStorage option is rather useless now (being unsafe to start with). Fix it nevertheless by saving credentials instead of keys.
* ...to be defined

# Table of Contents

  * [Installation](#installation)
  * [Usage](#usage)
    * [Global password protection](#global-password-protection)
    * [Password inventory](#password-inventory) **NEW**
    * [Secret from environment](#secret-from-environment)
    * [Customization](#default-vars-customization)
    * [Translations](#translations)
    * [Obfuscate pages](#obfuscate-pages)
  * [Features](#features)
    * [HighlightJS support](#highlightjs-support) *(default)*
    * [Arithmatex support](#arithmatex-support) *(default)*
    * [Mermaid2 support](#mermaid-support) *(default)*
    * [Tag encrypted page](#tag-encrypted-page) *(default)*
    * [Remember password](#remember-password)
    * [Encrypt something](#encrypt-something)
    * [Inject decrypt-form.tpl to theme](#inject-decrypt-formtpl-to-theme)
    * [Mix encrypted and normal content](#mix-encrypted-and-normal-content) **NEW**
    * [Search index encryption](#search-index-encryption)
    * [Search index encryption for mkdocs-material](#search-index-encryption-for-mkdocs-material)
    * [Override default templates](#override-default-templates)
    * [Add button](#add-button)
    * [Reload scripts](#reload-scripts)
    * [Self-host crypto-js](#self-host-crypto-js)
    * [File name obfuscation](#file-name-obfuscation)
    * [Signing of generated files](#signing-of-generated-files) **NEW**
  * [Contributing](#contributing)


# Installation

Install the package with pip:

```bash
pip install mkdocs-encryptcontent-plugin
```

Install the package from source with pip:

```bash
cd mkdocs-encryptcontent-plugin/
python setup.py sdist bdist_wheel
pip install --force-reinstall --no-deps dist/mkdocs_encryptcontent_plugin-3.0.0.dev2-py3-none-any.whl
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

Alternatively add the meta tag `level: secret` to use one or more secrets defined at the plugin's `password_inventory` in your `mkdocs.yml`.


## How does this work?

For every unique `password` and for every `level` we generate a random 256 bit key.
This key will be used for AES-256 encryption on every page with the same `password` or same `level`.
Optionally search entries and [encrypt something](#encrypt-something) on that page are also encrypted with the same key.

This random secret key (needed for deciphering the pages content) is then encrypted with another key that is derived from
the defined credentials (a password or a username/password pair).
The function to derive that key (PBKDF2) can be adjusted in calculation time (`kdf_pow`)
to make it harder for a brute force attacker to simply try all passwords.

## A word on password strength

The strength of a password can be measured in entropy or "possibilities to try" (for a brute force attacker).

For example take a tree character password with just lower case letters like "abc".  
The number of lower case letters is 26, so a three character password leads to 26 * 26 * 26 = 17 576 possibilities to try.

Now take a three character password which also includes upper case letters like "aBc".  
The number of possibilities per character doubles to 52, so the three character password leads to 52 * 52 * 52 = 140 608 possibilities.
So compared to "abc" we got **eight times** more entropy in this case.

So what happens if we add one character and still only use lower case letters, like "abcd"?  
It's 26^4 = 456 976 with a four character password, that's **26 times** more entropy compared to only using three lower case characters.

A brute force attacker will find a password after trying half the possibilities on average.
So the more entropy (possibilities to try) the better.
It's easier to get high entropy by increasing password size, than with adding more different characters or symbols.
An attacker could also have watched (or heard) you type the password (paying attention to the use of the shift key,
space bar or numeric keypad) and this way cross out character that you couldn't possibly have used.

So, to put it mildly: Every web page that forces you to use at least lower/upper case AND a number AND a symbol,
BUT only forces you to use eight characters of password size is not steering you to the right measures to gain entropy.

But, to be fair: A web page can take measures to seriously throttle the passwords try-able per second on the server side
or f.ex. use captchas after the third failed try. Although there were and most likely will be bad or failed examples of those measures.

This Mkdocs plugin can currently only take counter-measures to brute force attacks in form of PBKDF2,
so you should really be interested in choosing a strong password
(read [example1](https://en.wikipedia.org/wiki/Diceware) or [example2](https://xkcd.com/936/)).


### Global password protection

Add `global_password: your_password` in plugin configuration variable, to protect by default your articles with this password

```yaml
plugins:
    - encryptcontent:
        global_password: 'your_password'
```

If a password is defined in an article, it will **ALWAYS** overwrite the global password. 

> **NOTE** Keep in mind that if the `password:` tag exists without value in a page, it will **not be protected** !
> Use this to **disable** `global_password` on specific pages.


### Password inventory

With the `password_inventory` you can define protection levels (assigned with the meta tag `level` in markdown files).

```yaml
plugins:
    - encryptcontent:
        password_inventory:
          classified: 'password1'
          confidential:
            - 'password2'
            - 'password3'
          secret:
            user4: 'password4'
            user5: 'password5'
```

These levels may be only one password (f.ex. classified), a list of multiple passwords (f.ex. confidential) or multiple username/password pairs (f.ex. secret).
It is possible to reuse credentials at different levels.

>Note that a "list of multiple passwords" comes with a downside: All entries may be tested because unlike "user/password pairs"
>there is no hint to determine the distinct entry to try (At least I found no hint that wouldn't make it easier for a brute force attacker).
>This means, that a high `kdf_pow` could cause long waiting time even if the right password was entered.

The plugin will generate one secret key for each level, which is then used to encrypt the assigned sites.

It is good practice to assign the same level to all pages within a navigation branch,
this way the secret keys are taken from storage and one doesn't need to re-enter credentials.

- Start Page
- Help
- Secret Groups
    - Group alpha (level: alpha)
        - Sub Site A (level: alpha)
            - SubSub Site Aa(level: alpha)
        - Sub Site B (level: alpha)
    - Group beta (level: beta)
        - Sub Site A (level: beta)
        - Sub Site B (level: beta)
            - SubSub Site Ba (level: beta)

#### Password inventory in external file

You can define password levels in an external yaml file and use it with `password_file`.

```yaml
plugins:
    - encryptcontent:
        password_file: 'passwords.yml'
```

passwords.yml:
```yaml
classified: 'password1'
confidential:
    - 'password2'
    - 'password3'
secret:
    user4: 'password4'
    user5: 'password5'
```


#### Global password(s) in inventory

You can add the special level `_global`, which will be applied globally on all sites like this:

```yaml
plugins:
    - encryptcontent:
        password_inventory:
            _global: 'either define one password'
            _global:
                - 'or define'
                - 'multiple passwords'
            _global:
                user1: 'or use user'
                user2: 'and password pairs'
```

> **NOTE** Add the meta tag `level:` (without a value) to pages which should be excluded from global password level.
> Also note that it is always possible to set the page to a different level than the global one with the `level` meta tag.

### Secret from environment

It is possible to read values from environment variable (as discribed [here](https://www.mkdocs.org/user-guide/configuration/#environment-variables))

```yaml
plugins:
    - encryptcontent:
        password_inventory:
            secret:
                user1: !ENV PASSWORD1_FROM_ENV
                user2: !ENV [PASSWORD2_FROM_ENV, 'Password if PASSWORD2_FROM_ENV undefined or empty']
                user3: !ENV [PASSWORD3_FROM_ENV, FALLBACK_PASSWORD3_FROM_ENV, 'Password if neither PASSWORD3_FROM_ENV nor FALLBACK_PASSWORD3_FROM_ENV defined']
```

### Default vars customization

Optionally you can use some extra variables in plugin configuration to customize default messages.

```yaml
plugins:
    - encryptcontent:
        title_prefix: '[LOCK]'
        summary: 'another informational message to encrypted content'
        placeholder: 'another password placeholder'
        decryption_failure_message: 'another informational message when decryption fails'
        encryption_info_message: "another information message when you don't have access !"
        input_class: 'md-search__form md-search__input'
        button_class: 'md-search__icon'
```

Default prefix title is `[Protected]`.

Default summary message is `This content is protected with AES encryption.`.

Default password palceholder is `Provide password and press ENTER`.

Default decryption failure message is `Invalid password.`.

Defaut encryption information message is `Contact your administrator for access to this page.`.

> **NOTE** Adding a prefix to the title does not change the default navigation path !

### Translations

If the plugin is used in conjunction with the [static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/) plugin you can provide `translations` for the used `i18n_page_file_locale`.

```yaml
    - encryptcontent:
        #...
        translations:
          de:
            title_prefix: '[Verschlüsselt] '
            summary: 'Der Inhalt dieser Seite ist mit AES verschlüsselt. '
            placeholder: 'Mit Strg+Enter wird das Passwort global gesetzt'
            password_button_text: 'Entschlüsseln'
            decryption_failure_message: 'Falsches passwort.'
            encryption_info_message: 'Bitte wenden Sie sich an den Systemadministrator um auf diese Seite zuzugreifen.'
```

#### Custom per-page strings

You can set the  meta tag `encryption_summary` to customize `summary` and `encryption_info_message` on every page.

### Obfuscate pages

If you want to make it harder for search engines to scrape you pages content,
you can set `obfuscate: SomeNotSoSecretPassword` meta tag in markdown.

The page than will display `summary` and `encryption_info_message` together with a button labeled with
`password_button_text`. In order to view the pages content one hast to press the button first.

If a `password` or `level` is set, then the `obfuscate` feature will be disabled.
If you want to use `obfuscate` in a configuration where `global_password` or `_global` level is defined, 
you'll need to set the `password:` or rather `level:` meta tag (with no password/level defined) to undefine the password on this page.

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

You can add `tag_encrypted_page: False` in plugin configuration, to disable tagging of encrypted pages. 

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

### Remember password

Related to [issue #6](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/6)

> :warning: **This feature is not really secure !** decryption keys are store in clear text inside session storage.
>
> Instead of using this feature, I recommend to use a password manager with its web plugins.
> For example **KeepassXC** allows you, with a simple keyboard shortcut, to detect the password field `mkdocs-content-password` and to fill it automatically in a much more secure way.

If you do not have password manager, you can set `remember_password: True` in your `mkdocs.yml` to enable remember feature.

When enabled, each time you fill password form and press `Enter` and the password was correct (could be used to get the decryption key)
a key on session storage is create with the decryption key as value. 
When you reload the page, if you already have an 'encryptcontent' key in the session storage of your browser,
the page will be automatically decrypted using the value previously created.

By default, the key is created with a name relative to the page on which it was generated.
This 'relative' key will always be used as first attempt to decrypt the current page when loading.

If your password is a [global password](#global-password-protection), you can fill in the form
field  `mkdocs-content-password`, then use the keyboard shortcut `CTRL + ENTER` instead of the classic `ENTER`. 
The key that will be created with a generic name to making it accessible, by default, on all the pages of your site.

The form of decryption remains visible as long as the content has not been successfully decrypted, which allows in case of error to retry. 
These decryption keys are recreated every time the site is built, so they are only valid until the next `mkdocs build` or `mkdocs serve`.

```yaml
plugins:
    - encryptcontent:
        remember_password: True
```

> **NOTE** 
> Now The default is to use sessionStorage instead of localStorage, so the browser forgets the password after
> the current tab was closed. However it can be set to use localStorage by setting `session_storage: False`

### Encrypt something

Related to [issue #9](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/9)

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

2. Other example, with multiples target. In your custom Material theme, you want to encrypt ToC content and Footer.

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

Your configuration would look like this :
```yaml
plugins:
    - encryptcontent:
        encrypted_something:
            mkdocs-encrypted-toc: [nav, class]
            mkdocs-encrypted-footer: [div, id]
            mkdocs-encrypted-footer-meta: [div, id]
```

3. If you are using unmodified mkdocs-material, then this example will encrypt menu, toc and footer
But you'd need the Navigation pruning feature to hide the title of encrypted pages from navigation (or see 2.).

```yaml
plugins:
    - encryptcontent:
        encrypted_something:
            md-footer__inner: [nav, class]
            md-nav: [nav, class]
```

### Inject decrypt-form.tpl to theme

Some themes or plugins might interfere with the way this plugin encrypts the content of a page.
In this case this feature will find and encrypt a unique tag in the same way as `encrypted_something`
does and additionally inject its `decrypt-form.tpl.html` in front of it.

```yaml
plugins:
    - encryptcontent:
        inject:
            <uniq name>: [<html tag>, <'class' or 'id'>]
```

This is an example for mkdocs-material:
```yaml
plugins:
  - blog
  - encryptcontent:
        encrypted_something:
            md-footer__inner: [nav, class] #Footer
            md-nav: [nav, class] #Menu and toc
        inject:
            md-content: [div, class]
```

> This feature overrides the normal practice of replacing the rendered content of a page.

### Mix encrypted and normal content

It is possible to only encrypt parts of the page and also to remove parts on successful decryption.

First install PyMdown Extensions by entering `pip install --upgrade pymdown-extensions`,
then enable them in your `mkdocs.yml`:
```yaml
markdown_extensions:
    - pymdownx.blocks.html
```

This is an example of a mixed markdown page:

```
title: This page mixes encrypted and normal content
level: secret
inject_id: protected
delete_id: teaser

/// html | div#teaser
## Teaser

You won't believe which secrets this page will unveil.
Find out more after you enter the correct password...
///

/// html | div#protected
## Secret

Well, the princess is another castle.
///
```

The markdown externion enables us to wrap a div tag around content by `/// html | div#some-id`.
It ends with `///`. The meta tag `inject_id` defines which div id we would like to encrypt
(it also injects the decryption form here). And the div id found at `delete_id` will be deleted
on successfull decryption.

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
 * **dynamically** : Search index is encrypted on build. Search is possible once the pages have been decrypted.
 * **encrypted** : Search index of encrypted pages is removed on build. Search is not possible on encrypted pages.

You can set `search_index: '<mode_name>'` in your `mkdocs.yml` to change the search index encryption mode. Possible values are `clear`, `dynamically`, `encrypted`. The default mode is "**encrypted**".

```yaml
plugins:
    - encryptcontent:
        search_index: 'dynamically'
```

This functionality modifies the search index created by the “search” plug-in.
Some themes might override the default search plug-in provided by mkdocs, 
but so far the structure of the `search/search_index.json` file is consistent.

> The modification of the search index is carried out last (if `encryptcontent` is also last in `plugins`).
> But always double-check the generated index after `mkdocs build` to see if your information is protected.

When the configuration mode is set to "**dynamically**", the 
[javascripts contribution files](https://github.com/unverbuggt/mkdocs-encryptcontent-plugin/tree/master/encryptcontent/contrib/templates/search)
are used to override the default search plugin files provided by MkDocs. 
They include a process of decrypting and keeping the search index in a SessionStorage.

### Search index encryption for mkdocs-material

[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) uses a different search plugin that
cannot "easily" be overridden like the default search plugin.
However this Plugin will still remove encrypted pages (`encrypted`) or encrypt the search entries (`dynamically`)
for `mkdocs-material`.

In order to be able to decrypt the search index (`dynamically`) `mkdocs-material` needs to be customized (patched).

You'll need some [prerequisites](https://squidfunk.github.io/mkdocs-material/customization/#environment-setup)
and also execute these commands:

```bash
git clone https://github.com/squidfunk/mkdocs-material
cd mkdocs-material
pip install mkdocs-minify-plugin
pip install mkdocs-redirects
npm install

#copy material_search_worker.patch to mkdocs-material
patch -p 0 < material_search_worker.patch

pip install --force-reinstall .
#pip install --force-reinstall --no-deps . #faster if mkdocs-material was already installed
```

> Note: this currently doesn't work with mkdocs-material-9.x.x

### Override default templates

Related to [issue #32](https://github.com/CoinK0in/mkdocs-encryptcontent-plugin/issues/32)

You can override the default templates with your own templates by providing an actual replacement
path in the `html_template_path` *(HTML)* and `js_template_path` *(JS)* directives. 
Overridden templates **completely** replace the default templates. You **must** therefore copy the
default templates to keep this module working.

```yaml
plugins:
    - encryptcontent:
        html_template_path: "/root/real/path/mkdocs_poc/my_html_template.html"
        js_template_path: "/root/real/path/mkdocs_poc/my_js_template.js"
        input_class: 'md-search__form md-search__input'
        button_class: 'md-search__icon'
```

Use `input_class` and `button_class` to optionally set a CSS class for the password input field and the button.

When you overriding the default templates, you can add and use your own Jinja variables to condition
and enrich your template, by defining `html_extra_vars` and `js_extra_vars` directives in key/value format.
Added values can be used in your Jinja templates via the variable `extra`.

```yaml
plugins:
    - encryptcontent:
        html_extra_vars:
            my_extra: "extra value"
            <key>: <value>
        js_extra_vars:
            my_extra: "extra value"
            <key>: <value>
```

For example, you can modify your HTML template, to add a new title with your own text variable.

```jinja
[ ... ] 
<h2>{{ extra.my_extra }}</h2>
[ ... ]
```

> **NOTE** You must avoid replacing/overwriting the variables used by default by this module.
> The limitations are the same as those of the jinja models.
> Issues related to template override will not be addressed.

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
    - encryptcontent:
        reload_scripts:
            - 'js/example.js'
            - '#autoexec'
```

This feature now doesn't use JQuery anymore.

It is also possible to reload a script id like `<script id="autoexec">console.log('test');</script>` that was encrypted within the page (related to [issue #30](https://github.com/unverbuggt/mkdocs-encryptcontent-plugin/issues/30)).

### Self-host crypto-js

If you enable `selfhost` then you'll choose to upload crypto-js to your web server rather than using cloudflare CDN.
The self-host location is "SITE_URL/assets/javascripts/cryptojs/".

Additionally if you set `selfhost_download` then the required files will be automatically downloaded if needed.
The files are checked for their MD5 hash and saved to `docs_dir` or `selfhost_dir` (relative to `mkdocs.yml`).

```yaml
plugins:
    - encryptcontent:
        selfhost: true
        selfhost_download: false
        selfhost_dir: 'theme_overrides'
```

### File name obfuscation

Imagine your pages contain many images and you labeled them "1.jpg", "2.jpg" and so on for some reason.
If you'd like to encrypt one of these pages, an attacker could try guessing the image file names
and would be able to download them despite not having the password to the page.

This feature should make it impossible or at least way harder for an external attacker to guess the file names.
Please also check and disable directory listing for that matter.
Keep in mind that your hosting provider is still able to see all your images and files.

To counter file name guessing you could active the feature like this:

```yaml
plugins:
    - encryptcontent:
        selfhost: true
        selfhost_download: false
        hash_filenames:
          extensions:
            - 'png'
            - 'jpg'
            - 'jpeg'
            - 'svg'
          except:
            - 'lilien.svg'
```

At `extensions` we define which file name extensions to obfuscate
(extension is taken from the part after the last ".",
so the extension of "image.jpg" is "jpg" and of "archive.tar.gz" is "gz").

You can define multiple exceptions at the `except` list.
The file names that end with these strings will be skipped.
You should use this if some images are used by themes or other plugins.
Otherwise, you'd need to change these file names to the obfuscated ones.

The file names are obfuscated in a way that the corresponding file is hashed with MD5
and the hash is added to the file name
(If the file content is not changed the file name remains the same), like this:

some_image_1_bb80db433751833b8f8b4ad23767c0fc.jpg
("bb80db433751833b8f8b4ad23767c0fc" being the MD5 hash of said image.)

> The file name obfuscation is currently applied to the whole site - not just the encrypted pages...

### Signing of generated files

An attacker would most likely have a hard time brute forcing your encrypted content, given a good
password entropy. It would be much easier for him to fish for passwords by modifying the
generated pages, if he is able to hack your web space.

This feature will sign all encrypted pages and used javascript files with Ed25519. It will also generate
an example [canary script](https://en.wikipedia.org/wiki/Domestic_canary#Miner's_canary), which can be
customized to alert if files were modified.

> **NOTE** If Mkdocs is running with `mkdocs serve`, then signature verification of encrypted pages
> will most likely fail, because the files are modified by Mkdocs to enable live reload.

```yaml
      sign_files: 'signatures.json'
      sign_key: 'encryptcontent.key' #optional
      canary_template_path: '/path/to/canary.tpl.py' #optional
```

First an Ed25519 private key is generated at "encryptcontent.key" (besides `mkdocs.yml`), however you can supply an
existing private key as long as it's in PEM format.

After generation the signatures are saved to "signatures.json" in `site_dir`, so this file also needs to be uploaded
to the web space. The canary script will download this file and compare the URLs to its own list and then download
all files and verify the signatures.

As long as the private key used for signing remains secret, the canary script will be able to determine
if someone tampered with the files on the server. But you should run the canary script from another machine
that is not related to the server, otherwise the attacker could also modify the canary script or sign with his
private key instead.

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