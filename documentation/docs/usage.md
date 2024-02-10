# Usage

Add a tag like `password: secret password` to your pages [Meta-Data](https://www.mkdocs.org/user-guide/writing-your-docs/#yaml-style-meta-data) to protect them.

Alternatively add a meta tag like `level: secret` to use one or more secrets defined at the
plugin's `password_inventory` or `password_file` in your "mkdocs.yml" (see below).


## Password inventory

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

These levels may be only one password (f.ex. classified), a list of multiple passwords (f.ex. confidential)
or multiple username/password pairs (f.ex. secret).
It is possible to reuse credentials at different levels.

>Note that a "list of multiple passwords" comes with a downside: All entries may be tested because unlike "user/password pairs"
>there is no hint to determine the distinct entry to try
>(At least I found no hint that wouldn't make it easier for a brute force attacker).
>This means, that a high `kdf_pow` could cause long waiting time even if the right password was entered.

The plugin will generate one secret key for each level, which is then used to encrypt the assigned sites.

To indicate that your Markdown file should be encrypted for level "secret", add the following metadata at the beginning of the file:

```markdown
---
level: secret
---
This is the first paragraph of the document.
```


### Password inventory in external file

You can define password levels in an external yaml file and link it with `password_file`.
The intention is to separate sensitive information from configuration options.

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

## Global password protection

Add `global_password: your_password` in plugin configuration variable, to protect all pages with this password by default

```yaml
plugins:
    - encryptcontent:
        global_password: 'your_password'
```

If the password meta tag is defined in a markdown file, it will **ALWAYS** override the global password.

> **NOTE** Keep in mind that if the `password:` tag exists without value in a page, it will **not be protected** !
> Use this to **disable** `global_password` on specific pages.

### Global passwords in inventory

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

## Secret from environment

It is possible to read values from environment variable
(as discribed [here](https://www.mkdocs.org/user-guide/configuration/#environment-variables)).
This replaces the deprecated `use_secret` option from previous versions.

```yaml
plugins:
    - encryptcontent:
        password_inventory:
            secret:
                user1: !ENV PASSWORD1_FROM_ENV
                user2: !ENV [PASSWORD2_FROM_ENV, 'Password if PASSWORD2_FROM_ENV undefined or empty']
                user3: !ENV [PASSWORD3_FROM_ENV, FALLBACK_PASSWORD3_FROM_ENV, 'Password if neither PASSWORD3_FROM_ENV nor FALLBACK_PASSWORD3_FROM_ENV defined']
```

## Default vars customization

Optionally you can use some extra variables in plugin configuration to customize default strings.

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

## Translations

If the plugin is used in conjunction with the [static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/)
plugin you can provide `translations` for the used `i18n_page_locale`.

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

### Custom per-page strings

You can set the  meta tag `encryption_summary` to customize `summary` and `encryption_info_message` on every page.

## Obfuscate pages

If you want to make it harder for search engines to scrape you pages content,
you can set `obfuscate: SomeNotSoSecretPassword` meta tag in markdown.

The page then will display `summary` and `encryption_info_message` together with a button labeled with
`password_button_text`. In order to view the pages content one hast to press the button first.

If a `password` or `level` is set, then the `obfuscate` feature will be disabled.
If you want to use `obfuscate` in a configuration where `global_password` or `_global` level is defined,
you'll need to set the `password:` or rather `level:` meta tag (with no password/level defined) to undefine the password on this page.

The keys to all obfuscated pages are also saved in every keystore, so they are decrypted if someone entered
correct credentials.


## Example plugin configuration

```yaml
plugins:
    - encryptcontent:
        title_prefix: ''
        summary: ''
        placeholder: 'Password'
        placeholder_user: User
        password_button_text: 'ENTER'
        decryption_failure_message: 'Wrong user name or password.'
        encryption_info_message: 'Legitimation required.'
        translations:
          de:
            title_prefix: ''
            summary: ''
            placeholder: 'Passwort'
            placeholder_user: Benutzer
            password_button_text: 'ENTER'
            decryption_failure_message: 'Falscher Benutzer oder Passwort.'
            encryption_info_message: 'Legitimation erforderlich.'
        html_template_path: "decrypt-form.tpl.html" # override default html template
        password_button: True
        input_class: 'w3-input' # CSS class used for input username and password
        button_class: 'w3-button w3-theme-l1 w3-hover-theme' # CSS class for password_button
        hljs: False
        arithmatex: False
        mermaid2: False
        remember_keys: true # keys from keystore will temporarily saved to sessionStorage
        remember_password: false # the entered credentials are not saved
        remember_prefix: encryptcontent_plugin_ # use different prefixes if other sites are running on the same domain
        encrypted_something: # additionally encrypt some html elements
          #myNav: [div, id]
          myToc: [div, id]
          myTocButton: [div, id]
        search_index: 'dynamically' # dynamically encrypt mkdocs search index
        webcrypto: true # use browsers webcrypto support
        #selfhost: true # use self-hosted crypto-js
        #selfhost_download: true # download crypt-js for self-hosting
        #selfhost_dir: 'theme_override' # where to download crypto-js
        #reload_scripts:
        #  - '#theme'
        password_file: 'passwords.yml' # file with password inventory
        #kdf_pow: 4 # default for crypto-js: 4, default for webcrypto: 5
        sign_files: 'encryptcontent-plugin.json' # save ed25519 signatures here
        #hash_filenames: # add hash to file names of assets (to make them impossible to guess
        #  extensions:
        #    - 'png'
        #    - 'jpg'
        #    - 'jpeg'
        #    - 'svg'
        #  except:
        #    - 'logo.svg'
```
