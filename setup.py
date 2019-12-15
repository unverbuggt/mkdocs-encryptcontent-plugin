import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    with open(file_path) as file:
        content = file.read()
    return content if content else 'no content read'

class PyTest(TestCommand):
    user_options = []

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='mkdocs-encryptcontent-plugin',
    version='0.0.1',
    description='A MkDocs plugin that encrypt/decrypt markdown content with AES',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    keywords='mkdocs python markdown encrypt decrypt content',
    url='https://github.com/coink0in/mkdocs-encrypt-content-plugin/',
    author='CoinK0in',
    author_email='coink0in@protonmail.com',
    license='MIT',
    tests_require=[
        'pytest',
        'mkdocs',
        'pyyaml',
        'click',
    ],
    cmdclass = {'test': PyTest},
    python_requires='>=2.7.9,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    install_requires=[
        'mkdocs',
        'pyyaml',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    packages=find_packages(exclude=['*.tests']),
    entry_points={
        'mkdocs.plugins': [
            'encryptcontent = encryptcontent.plugin:encryptContentPlugin'
        ]
    },
    package_data={'encryptcontent': ['*.tpl.html']},
    include_package_data = True
)
