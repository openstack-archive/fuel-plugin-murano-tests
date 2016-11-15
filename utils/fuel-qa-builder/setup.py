#!/usr/bin/env python

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def get_requirements_list(requirements):
    all_requirements = read(requirements)
    all_requirements = [req for req in all_requirements.splitlines()
                        if 'launchpadlib' not in req]
    return all_requirements


setup(
    name='fuelweb_test',
    version=9.0,
    description='Fuel-qa fuelweb package',

    url='http://www.openstack.org/',
    author='OpenStack',
    author_email='openstack-dev@lists.openstack.org',
    packages=['fuelweb_test', 'gates_tests', 'core'],
    include_package_data=True,
    classifiers=[
        'Environment :: Linux',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=get_requirements_list('./fuelweb_test/requirements.txt'),
)
