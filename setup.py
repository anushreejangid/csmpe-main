# =============================================================================
#
# Copyright (c) 2016, Cisco Systems
# All rights reserved.
#
# # Author: Klaudiusz Staniek
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
# =============================================================================


from setuptools import setup, find_packages
import re
from uuid import uuid4


install_requires = [
    "stevedore",
    "pkginfo=1.3.2",
    "click",
    "condoor>=0.1.5",
    "sphinx",
    "sphinx_rtd_theme",
]


def version():
    pyfile = 'csmpe/__init__.py'
    with open(pyfile) as fp:
        data = fp.read()

    match = re.search("__version__ = '([^']+)'", data)
    assert match, 'cannot find version in {}'.format(pyfile)
    return match.group(1)


setup(
    name='csmpe',
    version=version(),
    description='CSM Plugin Engine',
    author='Klaudiusz Staniek',
    author_email='klstanie@cisco.com',
    url='https://github.com/csmserver/csmpe',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'csmpe = csmpe.__main__:cli',
        ],
        'csm.plugin': [
            '{} = csmpe.core_plugins.csm_get_inventory.ios_xr.plugin:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_get_inventory.ios_xe.plugin:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_get_inventory.nx_os.plugin:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_get_inventory.exr.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_config_capture.plugin:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_custom_commands_capture.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_failed_config_startup_check.ios_xr.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_check_config_filesystem.ios_xr.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_node_status_check.ios_xr.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_node_status_check.exr.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_node_status_check.ios_xe.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_redundancy_check.ios_xr.plugin:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_redundancy_check.ios_xe.plugin:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_error_core_check.ios_xr.plugin:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_check_isis_neighbors.ios_xr.plugin:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_filesystem_check.ios_xr.disk_space_check:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_filesystem_check.ios_xr.filesystem_rw_check:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.add:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.activate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.commit:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.deactivate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.remove:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.hardware_audit:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.pre_migrate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.migrate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xr.post_migrate:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_install_operations.exr.add:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.exr.activate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.exr.commit:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.exr.deactivate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.exr.remove:Plugin'.format(uuid4()),

            '{} = csmpe.core_plugins.csm_install_operations.ios_xe.add:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xe.pre_activate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xe.activate:Plugin'.format(uuid4()),
            '{} = csmpe.core_plugins.csm_install_operations.ios_xe.remove:Plugin'.format(uuid4()),
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    zip_safe=False,
    install_requires=install_requires,
    tests_require=['flake8'],
    package_data={'': ['LICENSE', ], },
)
