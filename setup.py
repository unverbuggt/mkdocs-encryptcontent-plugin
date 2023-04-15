import os
from setuptools import setup, find_packages


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    with open(file_path) as file:
        content = file.read()
    return content if content else 'no content read'


setup(
    name='mkdocs-encryptcontent-plugin',
    version='2.5.3',
    author='unverbuggt',
    author_email='unverbuggt@xn--rthlein-n2a.de',
    description='A MkDocs plugin that encrypt/decrypt markdown content with AES',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords='mkdocs python markdown encrypt decrypt content',
    url='https://github.com/unverbuggt/mkdocs-encryptcontent-plugin',
    license='MIT',
    python_requires='>=3.5',
    install_requires=[
        'mkdocs',
        'pyyaml',
        'pycryptodome',
        'beautifulsoup4',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    packages=find_packages(exclude=['*.tests']),
    entry_points={
        'mkdocs.plugins': [
            'encryptcontent = encryptcontent.plugin:encryptContentPlugin'
        ]
    },
    package_data={'encryptcontent': [
        '*.tpl.js',
        '*.tpl.html',
        'contrib/templates/search/*.js'
    ]},
    include_package_data=True
)
