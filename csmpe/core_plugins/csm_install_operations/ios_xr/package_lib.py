# =============================================================================
#
# Copyright (c) 2016, Cisco Systems
# All rights reserved.
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

import re

# from documentation:
# http://www.cisco.com/c/en/us/td/docs/routers/asr9000/software/asr9k_r5-3/sysman/configuration/guide/b-sysman-cg-53xasr9k/b-sysman-cg-53xasr9k_chapter_0100.html#con_57141

"""
For example,
disk0:asr9k-px-5.3.3.CSCuz33376-1.0.0

package_type = None
version_re = 5.3.3
smu_re = CSCuz33376
sp_re = None
subversion_re = 1.0.0
"""
platforms = ["asr9k", "hfr"]
package_types = "mini mcast mgbl mpls k9sec diags fpd doc bng li optic services services-infa " \
                "infra-test video 9000v asr901 asr903 ncs500x".split()
version_re = re.compile("(?P<VERSION>\d+\.\d+\.\d+(\.\d+\w+)?)")
smu_re = re.compile("(?P<SMU>CSC[a-z]{2}\d{5})")
sp_re = re.compile("(?P<SP>(sp|fp)\d{0,2})")
subversion_re = re.compile("(CSC|sp|fp).*(?P<SUBVERSION>\d+\.\d+\.\d+?)")


class SoftwarePackage(object):
    def __init__(self, package_name):
        # External Name: asr9k-asr9000v-nV-px.pie-6.1.2
        # Internal Name: asr9k-9000v-nV-px-6.1.2
        if 'asr9000v' in package_name:
            package_name = package_name.replace('asr9000v', '9000v')
        elif 'services-infra-px' in package_name:
            package_name = package_name.replace('-px', '')

        self.package_name = package_name

    @property
    def platform(self):
        for platform in platforms:
            if platform + "-" in self.package_name:
                return platform
        else:
            return None

    @property
    def package_type(self):
        for package_type in package_types:
            if "-" + package_type + "-" in self.package_name:
                return package_type
        else:
            return None

    @property
    def architecture(self):
        # asr9k-mcast-px.pie-5.3.2 (external name)
        # disk0:asr9k-mcast-px-5.3.2 (internal name)
        # asr9k-px-5.3.3.CSCuy81837.pie (external name)
        # disk0:asr9k-px-5.3.3.CSCuy81837-1.0.0 (internal name)
        if "-px" in self.package_name:
            return "px"
        else:
            return None

    @property
    def version(self):
        result = re.search(version_re, self.package_name)
        return result.group("VERSION") if result else None

    @property
    def smu(self):
        result = re.search(smu_re, self.package_name)
        return result.group("SMU") if result else None

    @property
    def sp(self):
        result = re.search(sp_re, self.package_name)
        return result.group("SP") if result else None

    @property
    def subversion(self):
        if self.sp or self.smu:
            result = re.search(subversion_re, self.package_name)
            return result.group("SUBVERSION") if result else None
        return None

    def is_valid(self):
        return self.platform and self.version and self.architecture and (self.package_type or self.smu or self.sp)

    def __eq__(self, other):
        result = self.platform == other.platform and \
            self.package_type == other.package_type and \
            self.architecture == other.architecture and \
            self.version == other.version and \
            self.smu == other.smu and \
            self.sp == other.sp and \
            (self.subversion == other.subversion if self.subversion and other.subversion else True)

        if result:
            # Append the disk location to the package name
            if ":" in self.package_name:
                disk = self.package_name.split(':')[0] + ":"
                if not other.package_name.startswith(disk):
                    other.package_name = disk + other.package_name

        return result

    def __hash__(self):
        return hash("{}{}{}{}{}".format(
            self.platform, self.package_type, self.architecture, self.version, self.smu, self.sp, self.subversion))

    @staticmethod
    def from_show_cmd(cmd):
        software_packages = set()
        data = cmd.split()
        for line in data:
            software_package = SoftwarePackage(line)
            if software_package.is_valid():
                software_packages.add(software_package)
        return software_packages

    @staticmethod
    def from_package_list(pkg_list):
        software_packages = set()
        for pkg in pkg_list:
            software_package = SoftwarePackage(pkg)
            if software_package.is_valid():
                software_packages.add(software_package)
        return software_packages

    def __repr__(self):
        return self.package_name

    def __str__(self):
        return self.__repr__()
