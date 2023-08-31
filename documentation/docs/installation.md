

# Installation

Install the package with pip:

```bash
pip install mkdocs-encryptcontent-plugin
```

Install the package from source with pip:

```bash
cd mkdocs-encryptcontent-plugin/
python setup.py sdist bdist_wheel
pip install --force-reinstall --no-deps dist/mkdocs_encryptcontent_plugin-3.0.0.dev3-py3-none-any.whl
```

Enable the plugin in your `mkdocs.yml`:

```yaml
plugins:
    - search: {}
    - encryptcontent: {}
```
> **NOTE:** If you have no `plugins` entry in your configuration file yet, you'll likely also want to add the `search` plugin.
> MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.
