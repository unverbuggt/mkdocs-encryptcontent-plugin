title: Security

## Security

### Crypto-js or webcrypto?

By default the plugin uses the crypto-js library for page decryption, but using
the browser's built-in webcrypto engine is also possible (set `webcrypto: True`).

The main advantage of webcrypto over crypto-js is that it is much faster, allowing higher
calculation difficulty for key derivation (`kdf_pow`). Also it may be easier to implement
key derivation functions other than PBKDF2 with webcrypto in the future.

On the other hand crypto-js is implemented in pure Javascript without dependencies and well
tested (but it probably won't receive any updates as development stalled in 2021)
and we know nothing about how good or bad webcrypto is implemented in different browsers.

#### Self-host crypto-js

If you enable `selfhost` then you'll choose to upload crypto-js to your web server rather than using cloudflare CDN.
The self-host location is "SITE_URL/assets/javascripts/cryptojs/".

Additionally if you set `selfhost_download` then the required files will be automatically downloaded if needed.
The files are checked for their MD5 hash and saved to `docs_dir` or `selfhost_dir` (relative to `mkdocs.yml`).

```yaml
plugins:
    - encryptcontent:
        selfhost: True
        selfhost_download: False
        selfhost_dir: 'theme_overrides'
```

#### KDF key generation caching

Either way (webcrypto or crypto-js) the [KDF](https://en.wikipedia.org/wiki/Key_derivation_function)
key generation needs to be done for each credential.
This may take some additional time when building the site, especially when there are many different ones.
That's why these keys and salt are cached by default to a yaml file named "encryptcontent.cache".

```yaml
plugins:
    - encryptcontent:
        cache_file: 'encryptcontent.cache' # change file name if needed
```

Caching can be disabled by setting `cache_file: ''`.


### File name obfuscation

Imagine your pages contain many images and you labeled them "1.jpg", "2.jpg" and so on for some reason.
If you'd like to encrypt one of these pages, an attacker could try guessing the image file names
and would be able to download them despite not having the password to the page.

This feature should make it impossible or at least way harder for an external attacker to guess the file names.
Please also check and disable directory listing for that matter.
Keep in mind that your hosting provider is still able to see all your images and files.

To counter file name guessing you could activate the feature like this:

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
> will fail, because the files are modified by Mkdocs to enable live reload.

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
that is not related to the server, otherwise the attacker could also modify the canary script and sign with his
private key instead.