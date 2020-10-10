#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'ged4py>=0.2',
    "pillow",
    "odfpy",
]

test_requirements = [
]

setup(
    name='ged2doc',
    version='0.5.0',
    description="Tools for converting GEDCOM data into document formats.",
    long_description=readme + '\n\n' + history,
    author="Andy Salnikov",
    author_email='ged4py@py-dev.com',
    url='https://github.com/andy-z/ged2doc',
    packages=find_packages(include=['ged2doc']),
    entry_points={
        'console_scripts': [
            'ged2doc=ged2doc.cli:main',
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='ged2doc',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Sociology :: Genealogy',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
