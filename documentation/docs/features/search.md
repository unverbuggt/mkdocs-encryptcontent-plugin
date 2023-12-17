## Search encryption

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

#### Material 8.x

You'll need some [prerequisites](https://squidfunk.github.io/mkdocs-material/customization/#environment-setup)
and also execute these commands:

```bash
git clone https://github.com/squidfunk/mkdocs-material
cd mkdocs-material
pip install mkdocs-minify-plugin
pip install mkdocs-redirects
npm install

#copy material_search_worker.patch to mkdocs-material
patch -p 0 < material_search_worker8.patch

pip install --force-reinstall .
#pip install --force-reinstall --no-deps . #faster if mkdocs-material was already installed
```

#### Material 9.x

Follow the instructions for [Theme development](https://squidfunk.github.io/mkdocs-material/customization/#theme-development) carefully.

Apply the patch before [Building the theme](https://squidfunk.github.io/mkdocs-material/customization/#building-the-theme):

```bash
patch -p 0 < material_browser_request9.patch # until Material 9.3
patch -p 0 < material_browser_request9_4p.patch # Material 9.4+
```

