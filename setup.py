#!/usr/bin/env python
#
# Copyright (c) 2018 Future Internet Consulting and Development Solutions S.L.
#
# This file is part of ckanext-ngsidata.
#
# Ckanext-right_time_context is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Ckanext-right_time_context is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Orion Context Broker. If not, see http://www.gnu.org/licenses/.

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ckanext-right_time_context',
    version='0.9',
    url='https://github.com/conwetlab/ckanext-right_time_context',
    author='CoNWeT Lab & FICODES',
    author_email='ckanextended@conwet.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[],
    include_package_data=True,
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    package_data={
    },
    data_files=[],
    tests_require=[
        'parameterized',
    ],
    test_suite='nosetests',
    entry_points='''
        [ckan.plugins]
        right_time_context=ckanext.right_time_context.plugin:NgsiView
    ''',
)
