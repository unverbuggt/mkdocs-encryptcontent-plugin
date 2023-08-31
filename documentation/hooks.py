import os
import logging
import hashlib
import sys
from urllib.request import urlopen
from os.path import exists
from pathlib import Path

from unittest.mock import patch

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_and_check(filename, url, hash):
    hash_md5 = hashlib.md5()
    logger = logging.getLogger("mkdocs.download_and_check")
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    if not exists(filename):
        Path(cur_dir + '/' + filename.rsplit('/',1)[0]).mkdir(parents=True, exist_ok=True)
        with urlopen(url) as response:
            filecontent = response.read()
            hash_md5.update(filecontent)
            hash_check = hash_md5.hexdigest()
            if hash == hash_check:
                with open(Path(cur_dir + '/' + filename), 'wb') as file:
                    file.write(filecontent)
                    logger.info('downloaded external asset "' + filename + '"')
            else:
                logger.error('error downloading asset "' + filename + '" hash mismatch!')
                os._exit(1)

def get_external_assets(config, **kwargs):
    download_and_check('theme_override/assets/javascripts/highlight.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js',
        '02d5118842743b5d6d73bba11e8dd63a')
    download_and_check('theme_override/assets/javascripts/languages/django.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/languages/django.min.js',
        '09fe95df12981e92e1cf678a0029a0f7')
    download_and_check('theme_override/assets/javascripts/tex-chtml.js',
        'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js',
        '1d4e370eb01c3768d4304e3245b0afa6')
    
    download_and_check('theme_override/assets/javascripts/output/chtml/fonts/woff-v2/MathJax_Zero.woff',
        'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/output/chtml/fonts/woff-v2/MathJax_Zero.woff',
        'b26f96047d1cb466c83e9b27bf353c1f')
    download_and_check('theme_override/assets/javascripts/output/chtml/fonts/woff-v2/MathJax_Math-Italic.woff',
        'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/output/chtml/fonts/woff-v2/MathJax_Math-Italic.woff',
        '5589d1a8fc62be6613020ef2fa13e410')
    download_and_check('theme_override/assets/javascripts/output/chtml/fonts/woff-v2/MathJax_Main-Regular.woff',
        'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/output/chtml/fonts/woff-v2/MathJax_Main-Regular.woff',
        '9995de4787f908d8237dba7007f6c3fe')
    download_and_check('theme_override/assets/javascripts/output/chtml/fonts/woff-v2/MathJax_Size3-Regular.woff',
        'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/output/chtml/fonts/woff-v2/MathJax_Size3-Regular.woff',
        'a7860eaf63c39f2603165893ce61a878')
    download_and_check('theme_override/assets/javascripts/output/chtml/fonts/woff-v2/MathJax_Size1-Regular.woff',
        'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/output/chtml/fonts/woff-v2/MathJax_Size1-Regular.woff',
        '7ee67b5348ee634dd16b968d281cb882')

    download_and_check('theme_override/assets/javascripts/mermaid.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/mermaid/9.4.3/mermaid.min.js',
        'e1bdcac49c3a6464a9aa3c6082b1833e')

def create_readme(config, **kwargs):
    logger = logging.getLogger("mkdocs.create_readme")
    cur_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    pypi_md = """[![PyPI Version][pypi-v-image]][pypi-v-link]
[![PyPI downloads](https://img.shields.io/pypi/dm/mkdocs-encryptcontent-plugin.svg)](https://pypi.org/project/mkdocs-encryptcontent-plugin)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)'

"""
    readme_file = cur_dir / Path('../README.md')

    with open(cur_dir / Path('docs/index.md'), "r") as f:
        index_md = f.read()
    readme_md = ''
    with open(cur_dir / Path('docs/installation.md'), "r") as f:
        readme_md = readme_md + f.read() + '\n'
    with open(cur_dir / Path('docs/usage.md'), "r") as f:
        readme_md = readme_md + f.read() + '\n'
    with open(cur_dir / Path('docs/features/index.md'), "r") as f:
        readme_md = readme_md + f.read() + '\n'
    with open(cur_dir / Path('docs/features/modifypages.md'), "r") as f:
        readme_md = readme_md + f.read() + '\n'
    with open(cur_dir / Path('docs/features/search.md'), "r") as f:
        readme_md = readme_md + f.read() + '\n'
    with open(cur_dir / Path('docs/features/jsext.md'), "r") as f:
        readme_md = readme_md + f.read() + '\n'
    with open(cur_dir / Path('docs/features/security.md'), "r") as f:
        readme_md = readme_md + f.read() + '\n'

    with open(readme_file, "w") as f:
        f.write(readme_md)
    logger.info('wrote README.md')
    try:
        with patch('sys.argv', ['','../README.md']):
            import markdowntoc
            markdowntoc.main()
    except:
        logger.error('Please run "pip install markdown-toc"')

    with open(readme_file, "r") as f:
        readme_md = f.read()
    with open(readme_file, "w") as f:
        f.write(pypi_md + index_md + readme_md)
