# mkdocs-encryptcontent-plugin

This plugin allows you to have password protected articles and pages in MKdocs.

The content is encrypted with AES-256 in Python using PyCryptodome and decrypted in the browser with Crypto-JS or Webcrypto.

*It has been tested in Python Python 3.8+*

**Usecase**

> I want to be able to protect the content of the page with a password.
>
> Define a password to protect each page independently or a global password to protect them all.
>
> If a global password exists, all articles and pages are protected with this password.
>
> If a password is defined in an article or a page, it is always used even if there is a global password.
>
> If a password is defined as an empty character string, content encryption is disabled.
>
> Additionally password levels can be defined in mkdocs.yml or external yaml file with user/password credentials.

## Todos for 3.0.x

* ~~Rework password handling or inventory of some sort~~
* ~~Rework crypto (PBKDF2 + AES256)~~
* ~~Save the generated random keys instead of passwords to session storage (remember_keys)~~
* ~~Sign generated generated and javascript files used in encrypted pages to make it more tamper proof~~
* ~~Add urlencode for latin1 encoding in passwords, as it pycryptodome's implementation of PBKDF2 requires it~~
* ~~find an equivalent way to define multiple passwords in the password inventory as global password~~
* ~~make it possible to define passwords in external yaml file(s)~~
* ~~decrypt all possible keys by one login (replace path fallback)~~
* ~~optional replace crypto-js by webcrypto functions~~
* ~~localStorage option is rather useless now (being unsafe to start with). Fix it nevertheless by saving credentials instead of keys~~
* Update/Restructure documentation

## Todos for 3.1.x
* optional server side keystore (allows throtteling)
* ...to be defined
