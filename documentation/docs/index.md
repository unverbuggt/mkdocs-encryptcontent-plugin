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

## New features (compared to version 2.5.x)

* Stronger cryptography (PBKDF2 for key derivation)
* Faster cryptography (Webcrypto as alternative to crypto-js)
* Allow password inventory or levels in mkdocs.yml or external file for credential handling
* Allow user name + password as credentials
* If credential is reused in different levels it also decrypts all of their content
* Optional adding of credentials to URLs for sharing
* Optional tamper check by signing generated files with Ed25519
* New [Documentation](https://unverbuggt.github.io/mkdocs-encryptcontent-plugin/) and [Test bench](https://unverbuggt.github.io/mkdocs-encryptcontent-plugin/testbench/)

## Upgrading from version 2.5.x

The `use_secret` functionality was discontinued in the plugin configuration and as a meta tag.

In order to use environment variables in user names or passwords, use the 
[special yaml tag](https://www.mkdocs.org/user-guide/configuration/#special-yaml-tags) `!ENV`.

## Todos for 3.1.x
* optional server side keystore (allows throtteling)
* ...to be defined
