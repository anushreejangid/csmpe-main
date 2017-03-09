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


import os

from csmpe.plugins import CSMPlugin
from utils import get_filesystems


class Plugin(CSMPlugin):
    """This plugin captures custom commands and stores in the log directory."""
    name = "Disk Space Check Plugin"
    platforms = {'ASR9K', 'CRS'}
    phases = {'Pre-Add'}
    os = {'XR'}

    def _get_pie_size(self, package_url):
        """
        # admin show install pie-info ftp://terastream:*****@172.20.168.195//home/terastream/4.3.1FCS/asr9k-doc-px.pie-4.3.1
        Contents of pie file '/ftp://terastream:*****@172.20.168.195//home/terastream/4.3.1FCS/asr9k-doc-px.pie-4.3.1':
            Expiry date       : < NOT AVAILABLE
            Uncompressed size : 25792000
            Compressed size   : 5602232
            Size on disk      : 5668352

            asr9k-doc-px-4.3.1
                asr9K-doc-supp-4.3.1
        """
        cmd = "admin show install pie-info " + package_url
        output = self.ctx.send(cmd, timeout=3600)
        if output:
            for line in output.split('\n'):
                if "Compressed" in line:
                    size = long(line.split(":")[1].strip())
                    return size
                if line and line[:6] == "Error:":
                    self.ctx.error(output)

    def run(self):
        try:
            packages = self.ctx.software_packages
        except AttributeError:
            self.ctx.warning("No package list provided. Skipping calculation of required free harddisk space.")
            return

        try:
            server_repository_url = self.ctx.server_repository_url
        except AttributeError:
            self.ctx.warning("No repository path provided.")
            return

        if server_repository_url[:4] != 'tftp' and server_repository_url[:3] != 'ftp':
            self.ctx.info('Skipping as disk space check only works for TFTP/FTP.')
            return

        file_systems = get_filesystems(self.ctx)
        disk0 = file_systems.get('disk0:', None)
        if disk0:
            disk0_free = disk0.get('free', 0)
        else:
            self.ctx.error("No filesystem 'disk0:' on active RP.")
            return

        total_size = 0
        for package in packages:
            if package == "":
                continue

            if 'pie' not in package:
                self.ctx.info("Package: {} cannot be checked, disk space check result will not be accurate.".format(package))
                continue

            package_url = os.path.join(server_repository_url, package)
            size = self._get_pie_size(package_url)
            total_size += size
            self.ctx.info("Package: {} requires {} bytes.".format(package, size))

        self.ctx.info("Total (required/available): {}/{} bytes".format(total_size, disk0_free))
        if disk0_free < total_size:
            self.ctx.error("Not enough space on disk0: to install packages. The install process can't proceed.")
        else:
            self.ctx.info("There is enough space on disk0: to install packages.")
        return True
