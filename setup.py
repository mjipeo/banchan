#!/usr/bin/env python

from codecs import open
import os
import sys

import banchan

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = [
    'banchan',
]

requires = []

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

setup(
    name='banchan',
    version=banchan.__version__,
    description='Collection of small Python utilities',
    long_description=readme,
    author='Minjong Chung',
    author_email='mjipeo@gmail.com',
    url='https://github.com/mjipeo/banchan',
    packages=packages,
    package_data={},
    package_dir={'banchan': 'banchan'},
    include_package_data=True,
    install_requires=requires,
    license='Apache 2.0',
    zip_safe=False,
    classifiers=(),
)
