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

from csmpe.plugins import CSMPlugin
from install import install_add_remove
from csmpe.core_plugins.csm_get_inventory.ios_xr.plugin import get_package, get_inventory


class Plugin(CSMPlugin):
    """This plugin adds packages from repository to the device."""
    name = "Install Add Plugin"
    platforms = {'ASR9K', 'CRS'}
    phases = {'Add'}
    os = {'XR'}

    def install_add(self, server_repository_url, s_packages, has_tar=False):
        if server_repository_url.startswith("scp"):
            # scp username:password@x.x.x.x:/home_directory destination_on_host
            scp_username_and_password, sep, server_and_directory_and_destination = server_repository_url.partition('@')
            # scp_username_and_password = 'scp username:password', sep = '@',
            # server_ip_and_directory = 'x.x.x.x:/home_directory destination_on_host'
            if not scp_username_and_password or not sep or not server_and_directory_and_destination:
                self.ctx.error("Check if the SCP server repository is configured correctly on CSM Server.")

            scp_username, sep, scp_password = scp_username_and_password.partition(':')
            if not scp_username or not sep or not scp_password:
                self.ctx.error("Check if the SCP server repository is configured correctly on CSM Server.")

            server_and_directory, sep, destination_on_host = server_and_directory_and_destination.partition(' ')
            if not server_and_directory or not sep or not destination_on_host:
                self.ctx.error("Check if the SCP server repository is configured correctly on CSM Server.")

            # scp username:@x.x.x.x:/home_directory
            url = scp_username + '@' + server_and_directory
            for package in s_packages.split():
                cmd = "{}/{} {}".format(url, package, destination_on_host)

            cmd = "admin install add source {} {} async".format(destination_on_host, s_packages)
        else:
            cmd = "admin install add source {} {} async".format(server_repository_url, s_packages)

        install_add_remove(self.ctx, cmd, has_tar=has_tar)

    def run(self):
        server_repository_url = self.ctx.server_repository_url

        if server_repository_url is None:
            self.ctx.error("No repository provided")
            return

        packages = self.ctx.software_packages
        if packages is None:
            self.ctx.error("No package list provided")
            return

        has_tar = False

        s_packages = " ".join([package for package in packages
                               if '-vm' not in package and ('pie' in package or 'tar' in package)])
        if 'tar' in s_packages:
            has_tar = True

        if not s_packages:
            self.ctx.error("None of the selected package(s) has an acceptable file extension.")

        self.ctx.info("Add Package(s) Pending")
        self.ctx.post_status("Add Package(s) Pending")

        self.install_add(server_repository_url, s_packages, has_tar=has_tar)

        self.ctx.info("Package(s) Added Successfully")

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)
