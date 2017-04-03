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

"""
NCS4K

Production Packages

External Names                                Internal Names
ncs4k-full-x.iso-6.0.2
ncs4k-mini-x.iso-6.0.2
ncs4k-k9sec.pkg-6.0.2
ncs4k-mpls.pkg-6.0.2
ncs4k-mcast.pkg-6.0.2
ncs4k-mgbl.pkg-6.0.2

NCS6K

Production Packages

External Names                                Internal Names
ncs6k-doc.pkg-5.2.4                           ncs6k-doc-5.2.4
ncs6k-li.pkg-5.2.4                            ncs6k-li-5.2.4
ncs6k-mcast.pkg-5.2.4                         ncs6k-mcast-5.2.4
ncs6k-mgbl.pkg-5.2.4                          ncs6k-mgbl-5.2.4
ncs6k-mini-x.iso-5.2.4                        ncs6k-mini-x-5.2.4
ncs6k-mpls.pkg-5.2.4                          ncs6k-mpls-5.2.4
ncs6k-sysadmin.iso-5.2.4                      ncs6k-sysadmin-5.2.4
ncs6k-full-x.iso-5.2.4                        ncs6k-full-x-5.2.4
ncs6k-5.2.5.CSCuy47880.smu                    ncs6k-5.2.5.CSCuy47880-1.0.0  <- subversion added

Engineering Packages

External Names                                Internal Names
ncs6k-mcast.pkg-5.2.5.47I.DT_IMAGE            ncs6k-mcast-5.2.5.47I
ncs6k-mini-x.iso-6.1.0.07I.DT_IMAGE           ncs6k-xr-5.2.5.47I
ncs6k-5.2.5.47I.CSCuy47880-0.0.4.i.smu        ncs6k-5.2.5.47I.CSCuy47880-0.0.4.i

ASR9K-64

Production Packages - not finalized yet

External Names                                Internal Names
asr9k-mcast-x64-2.0.0.0-r611.x86_64.rpm       asr9k-mcast-x64-2.0.0.0-r611
asr9k-bgp-x64-1.0.0.0-r611.x86_64.rpm         asr9k-bgp-x64-1.0.0.0-r611
asr9k-mgbl-x64-3.0.0.0-r611.x86_64.rpm        asr9k-mgbl-x64-3.0.0.0-r611
asr9k-full-x64.iso-6.1.1                      asr9k-xr-6.1.1
asr9k-mini-x64.iso-6.1.1                      asr9k-xr-6.1.1

Engineering Packages

External Names                                                          Internal Names
asr9k-mcast-x64-2.0.0.0-r61116I.x86_64.rpm-6.1.1.16I.DT_IMAGE           asr9k-mcast-x64-2.0.0.0-r61116I
asr9k-bgp-x64-1.0.0.0-r61116I.x86_64.rpm-6.1.1.16I.DT_IMAGE             asr9k-bgp-x64-1.0.0.0-r61116I
asr9k-mgbl-x64-3.0.0.0-r61116I.x86_64.rpm-6.1.1.16I.DT_IMAGE            asr9k-mgbl-x64-3.0.0.0-r61116I
asr9k-full-x64.iso-6.1.1.16I.DT_IMAGE                                   asr9k-full-x64-6.1.1.16I
asr9k-mini-x64.iso-6.1.1.16I.DT_IMAGE                                   asr9k-mini-x64-6.1.1.16I

NCS5K

Production Packages

External Names                                Internal Names
ncs5k-sysadmin.iso-6.0.1                      ncs5k-sysadmin-6.0.1
ncs5k-full-x.iso-6.0.1                        ncs5k-xr-6.0.1
ncs5k-mini-x.iso-6.0.1                        ncs5k-xr-6.0.1
ncs5k-mcast-2.0.0.0-r601.x86_64.rpm-6.0.1     ncs5k-mcast-2.0.0.0-r601
ncs5k-mgbl-2.0.0.0-r601.x86_64.rpm-6.0.1      ncs5k-mgbl-2.0.0.0-r601
ncs5k-mpls-2.0.0.0-r601.x86_64.rpm-6.0.1      ncs5k-mpls-2.0.0.0-r601
ncs5k-k9sec-2.0.0.0-r601.x86_64.rpm-6.0.1     ncs5k-k9sec-2.0.0.0-r601
ncs5k-isis-2.0.0.0-r601.x86_64.rpm-6.0.1      ncs5k-isis-2.0.0.0-r601
ncs5k-ospf-2.0.0.0-r601.x86_64.rpm-6.0.1      ncs5k-ospf-2.0.0.0-r601

Engineering Packages

External Names                                                Internal Names
ncs5k-mgbl-x64-3.0.0.0-r61116I.x86_64.rpm-6.0.1.16I.DT_IMAGE  ncs5k-mgbl-3.0.0.0-r60116I
ncs5k-sysadmin.iso-6.0.1                                      ncs5k-sysadmin-6.0.1.26I
ncs5k-full-x.iso-6.0.1.16I.DT_IMAGE                           ncs5k-xr-6.0.1.16I

NCS5500

Production Packages

External Names                                                Internal Names
ncs5500-eigrp-2.0.0.0-r601.x86_64.rpm-6.0.1                   ncs5500-eigrp-2.0.0.0-r601
ncs5500-isis-2.0.0.0-r601.x86_64.rpm-6.0.1                    ncs5500-isis-2.0.0.0-r601
ncs5500-k9sec-2.0.0.0-r601.x86_64.rpm-6.0.1                   ncs5500-k9sec-2.0.0.0-r601
ncs5500-m2m-2.0.0.0-r601.x86_64.rpm-6.0.1                     ncs5500-m2m-2.0.0.0-r601
ncs5500-mgbl-3.0.0.0-r601.x86_64.rpm-6.0.1                    ncs5500-mgbl-3.0.0.0-r601
ncs5500-mini-x.iso-6.0.1                                      ncs5500-xr-6.0.1
ncs5500-mpls-te-rsvp-2.0.0.0-r601.x86_64.rpm-6.0.1            ncs5500-mpls-te-rsvp-2.0.0.0-r601
ncs5500-mpls-2.0.0.0-r601.x86_64.rpm-6.0.1                    ncs5500-mpls-2.0.0.0-r601
ncs5500-ospf-1.0.0.0-r601.x86_64.rpm-6.0.1                    ncs5500-ospf-1.0.0.0-r601
ncs5500-parser-1.0.0.0-r601.x86_64.rpm-6.0.1                  ncs5500-parser-1.0.0.0-r601
"""
import re

platforms = ['asr9k', 'ncs1k', 'ncs4k', 'ncs5k', 'ncs5500', 'ncs6k', 'xrv9k']


version_dict = {"asr9k ncs1k ncs5k ncs5500 xrv9k":  # 61117I or 611 or 6.1.1.17I or 6.1.1
                re.compile("(?P<VERSION>(\d+\d+\d+(\d+\w+)?)|(\d+\.\d+\.\d+(\.\d+\w+)?)(?!\.\d)(?!-))"),
                "ncs4k ncs6k":                      # 5.2.4 or 5.2.4.47I
                re.compile("(?P<VERSION>\d+\.\d+\.\d+(\.\d+\w+)?)"),
                }

smu_re = re.compile("(?P<SMU>CSC[a-z]{2}\d{5})")

subversion_dict = {"asr9k ncs1k ncs5k ncs5500 xrv9k":
                   re.compile("-(?P<SUBVERSION>\d+\.\d+\.\d+\.\d+)-"),  # 2.0.0.0
                   "ncs4k ncs6k":
                   re.compile("CSC.*(?P<SUBVERSION>\d+\.\d+\.\d+?)"),   # 0.0.4
                   }


class SoftwarePackage(object):
    def __init__(self, package_name):
        self.package_name = package_name

        self._platform = None
        self._package_type = None
        self._version = None
        self._smu = None
        self._subversion = None

    @property
    def platform(self):
        if not self._platform:
            for platform in platforms:
                if platform + "-" in self.package_name:
                    self._platform = platform
                    break

        return self._platform

    @property
    def package_type(self):
        if not self._package_type:
            # For ASR9K-X64, NCS1K, NCS5K, NCS5500:
            #     Extract the package type string before X.X.X.X
            # For NCS6K
            #     Extract the package type string before X.X.X
            pattern = '-\d+\.\d+\.\d+' if self.platform == 'ncs6k' or \
                self.platform == 'ncs4k' else '-\d\.\d\.\d.\d'

            if self.platform and self.platform in self.package_name:
                match = re.search(pattern, self.package_name)

                # Special handling for mini, full, and sysadmin ISO on ASR9K-X64, NCS1K, NCS5K, NCS5500
                # Example: ncs5500-mini-x.iso-6.0.1, asr9k-full-x64.iso-6.1.1
                # Package type string is before the 3 part version string

                # External Name: ncs5k-goldenk9-x.iso-6.3.1.11I.0, Internal Name: ncs5k-goldenk9-x-6.3.1.11I
                if not match and sum([x in self.package_name for x in ['full', 'mini', 'sysadmin', 'goldenk9']]) > 0:
                    # Use the three part match for these ISO packages
                    match = re.search('-\d+\.\d+\.\d+', self.package_name)

                if match:
                    # Extract the package type
                    self._package_type = self.package_name[0:match.start()].replace(self.platform + '-', '')

                if self._package_type:
                    # Takes care the external to internal name matching
                    # Example, ncs6k-mgbl.pkg-5.2.5 -> mgbl, ncs5500-mini-x.iso-6.0.1 -> mini-x
                    self._package_type = self._package_type.replace('.pkg', '').replace('.iso', '')

        return self._package_type

    @property
    def version(self):
        if not self._version:
            dict_values = self.get_values(version_dict, self.platform)
            if self.platform and dict_values:
                to_match = self.package_name.replace(self.platform, '')
                result = re.search(dict_values, to_match)
                if result:
                    self._version = result.group("VERSION")

        return self._version

    @property
    def smu(self):
        if not self._smu:
            result = re.search(smu_re, self.package_name)
            if result:
                self._smu = result.group("SMU")

        return self._smu

    @property
    def subversion(self):
        if not self._subversion:
            dict_values = self.get_values(subversion_dict, self.platform)
            if self.platform and dict_values:
                # For NCS6K, only need to consider subversion if it is a SMU.
                if self.platform in ["asr9k", "ncs1k", "ncs5k", "ncs5500", "xrv9k"] or self.smu:
                    to_match = self.package_name.replace(self.platform, '')
                    result = re.search(dict_values, to_match)
                    if result:
                        self._subversion = result.group("SUBVERSION")

        return self._subversion

    def get_values(self, dictionary, key):
        for keys in dictionary.keys():
            if key in keys.split():
                return dictionary.get(keys)
        return None

    def is_valid(self):
        return self.platform and self.version and (self.package_type or self.smu)

    def __eq__(self, other):
        result = self.platform == other.platform and \
            (self.package_type == other.package_type) and \
            self.version == other.version and \
            self.smu == other.smu and \
            (self.subversion == other.subversion if self.subversion and other.subversion else True)

        return result

    def __hash__(self):
        return hash("{}{}{}{}{}".format(
            self.platform, self.package_type, self.version, self.smu, self.subversion))

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
                """ for debugging
                print('package_name', software_package.package_name,
                      'platform', software_package.platform, 'package_type', software_package.package_type,
                      'version', software_package.version, 'smu', software_package.smu,
                      'subversion', software_package.subversion)
                """
                software_packages.add(software_package)
        return software_packages

    def __repr__(self):
        return self.package_name

    def __str__(self):
        return self.__repr__()
