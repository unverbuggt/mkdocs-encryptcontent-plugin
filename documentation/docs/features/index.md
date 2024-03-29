# Features

## Override default templates

Related to [issue #32](https://github.com/unverbuggt/mkdocs-encryptcontent-plugin/issues/32)

You can override the default templates with your own templates by providing an actual replacement
path in the `html_template_path` *(HTML)* and `js_template_path` *(JS)* directives. 
Overridden templates **completely** replace the default templates. You **must** therefore copy the
default templates as a starting point to keep this plugin working.

```yaml
plugins:
    - encryptcontent:
        html_template_path: "/root/real/path/mkdocs_poc/my_html_template.html"
        js_template_path: "/root/real/path/mkdocs_poc/my_js_template.js"
        form_class: 'md-content__inner md-typeset'
        input_class: 'md-input'
        button_class: 'md-button md-button--primary'
```

Use `form_class`, `input_class` and `button_class` to optionally set a CSS class for the password input field and the button.

When overriding the default templates, you can add and use your own Jinja variables
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

> **NOTE** Issues related to template override will not be addressed.

## Add button

Add `password_button: True` in plugin configuration variable, to add a button to the right of the password field.

When enabled, it allows to decrypt the content just like the classic keypress ENTER.

Optionally, you can add `password_button_text: 'custom_text_button'` to customize the button text.
 
```yaml
plugins:
    - encryptcontent:
        password_button: True
        password_button_text: 'custom_text_button'
```

## Tag encrypted page

> **Enable by default**

Related to [issue #7](https://github.com/unverbuggt/mkdocs-encryptcontent-plugin/issues/7)

This feature adds an additional attribute `encrypted` with value `True` to the mkdocs type `mkdocs.nav.page` object.

You can add `tag_encrypted_page: False` in plugin configuration, to disable tagging of encrypted pages. 

When enabled, it is possible to use the `encrypted` attribute in the jinja template of your theme, as a condition to perform custom modification.

```jinja
{%- for nav_item in nav %}
    {% if nav_item.encrypted %}
        <!-- Do something --> 
    {% endif %}
{%- endfor %}
```

For example, you can use conditional check to add a custom class:

```jinja
<a {% if nav_item.encrypted %}class="mkdocs-encrypted-class"{% endif %}href="{{ nav_item.url|url }}">{{ nav_item.title }}</a>
```

## Remember password

Related to [issue #6](https://github.com/unverbuggt/mkdocs-encryptcontent-plugin/issues/6)

By default the plugin will save the decrypted AES keys to session storage of the browser (can be disabled by setting `remember_keys: False`).
This is enabled for convenience, so you are able to browse between multiple encrypted pages without having to re-enter the password.

Additionally it is possible to save the entered user/password in session storage (setting `remember_password: True`). Use this for
additional convenience during `mkdocs serve`, because the AES key are regenerated every time MkDocs starts
(rendering the old ones invalid and requiring to re-enter a valid credential again).

To avoid problems when multiple sites are hosted within the same domain, it is possible to customize the name of
the keys saved to storage with `remember_prefix`.

> **This feature is not really secure !** decryption keys are store in clear text inside session storage.
>
> Instead of using these features, I recommend to use a password manager with its browser plugin.
> For example **KeepassXC** allows you to detect the password field
> `mkdocs-content-password` and fill it automatically in a much more secure way.

It is also possible to save the used credentials permanently to local storage (setting `session_storage: False`), but
this should only be done for testing purposes. The local storage of a browser is most likely readable
for every other process that can access the file system. 

The session storage however should only be located in memory and be forgotten after the browser tab is closed.

```yaml
plugins:
    - encryptcontent:
        remember_keys : True
        remember_password: False
        remember_prefix: secretsite_
```

## Share link generation

It is possible to share valid credentials by adding them to the hash part of the URL.
The plugin can also generate share links for certain pages if the meta tag `sharelink: true`
is defined in markdown.
It will use the first credential for the pages level or the pages password.
The credentials for auto-generated links are base64url encoded.

```yaml
plugins:
    - encryptcontent:
        sharelinks: True
        sharelinks_output: 'sharelinks.txt' # generated share links are saved here
```
> One condition applies: The user name must not contain the ":" character (Passwords may use that character).

However if `sharelinks: True` is enabled in the plugin configuration you can generate share links yourself:\
`https://your-domain.com/your-site/protected-page/#!username:password` for user/password or\
`https://your-domain.com/your-site/protected-page/#!password` for only password.

> Then another condition applies: If non-aphanumeric characters are used in user/password,
> they need to be URLencoded (f.ex. %20 = space character). Some browsers may do that automatically (Do a copy/paste from the browsers address bar then).

### Incomplete Share links

Since version 3.0.3 it is possible to leave out one part of the password when share links are generated via meta tag.
To do this use the ":" character in a password to divide the part that is incorporated to the share link and the part that remains secret,
like "PartThatIsEncodedToTheShareLink:PartThatRemainsSecret". 
The feature is enabled by setting the option `sharelinks_incomplete: true`.
If the password that is read from the share link ends with the ":" character, then an additional password input field is displayed for entering the secret part.

> If the feature is used, then passwords must not end with the ":" character.


## Storage of additional variables in keystore

Since version 3.0.3 it is possible to set arbitrary session store variables after decryption.
These can be used by javascript functions f. ex. to read API tokens or show the user name or set visibility of menu entries.
The variables are encrypted together with the content keys in the keystore.

```yaml
plugins:
    - encryptcontent:
        additional_storage_file: 'additional_storage.yaml'
```

The file may contain a `userpass:` dictionary, wich refers to user names
and/or a `password:` dictionary, that refers to password-only credentials.
It may contain a arbitrary number of key/value pairs,
but keep in mind to check if the key name is reasonable and not already used by other parts of the page
(as it will be overwritten after decryption).

```yaml
userpass:
  alice:
    username: Alice McAliceface
    userid: 1
    token: uCZDqa2vzuSPFX-o9TebinUAnD9sePJqpPYhavMkCH7gGo7lhjWRS17-HgBys9UKnFR37zXO4Q_f1_ywZJqBlA==

password:
  Head32_Sculpture_bovine_:
    username: Head McPassword
```