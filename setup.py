#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='thehivebeebot',
    version='1.0.0',
    description='The Hive automation of Cortex analysis program.',
    long_description='',
    author='Rémi ALLAIN',
    author_email='rallain@cyberprotect.fr',
    maintainer='Rémi ALLAIN',
    url='https://github.com/Cyberprotect/TheHiveBeeBot',
    license='AGPL-V3',
    packages=['thehivebeebot'],
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    include_package_data=True,
    install_requires=['future', 'requests', 'python-magic', 'thehive4py']
)
