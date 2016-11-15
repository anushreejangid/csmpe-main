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


# from package_lib import SoftwarePackage
from csmpe.plugins import CSMPlugin
from install import install_activate_reload
from install import install_activate_write_memory
from csmpe.core_plugins.csm_get_inventory.ios.plugin import get_package, get_inventory
from csmpe.core_plugins.csm_install_operations.utils import update_device_info_udi


class Plugin(CSMPlugin):
    """This plugin Activates packages on the device."""
    name = "Install Activate Plugin"
    platforms = {'ASR900'}
    phases = {'Activate'}
    os = {'IOS'}

    def run(self):
        """
        Performs install activate operation
        """

        self.ctx.info("Hardware platform: {}".format(self.ctx._connection.platform))
        self.ctx.info("OS Version: {}".format(self.ctx._connection.os_version))

        try:
            packages = self.ctx.software_packages
        except AttributeError:
            self.ctx.warning("No package list provided. Skipping calculation of required free bootflash memory.")
            return

        pkg = ''.join(packages)

        if not pkg.startswith("asr901"):
            self.ctx.error('Unsupported image type for {} while Activate package = '
                           '{}'.format(self.ctx._connection.platform, pkg))

        self.ctx.info("Activate package(s) pending")
        self.ctx.post_status("Activate Package(s) Pending")

        prompt = self.ctx._connection.hostname

        # configurations
        cmd = "configure terminal"
        self.ctx.send(cmd, wait_for_string=prompt)
        cmd = "config-register 0x2102"
        self.ctx.send(cmd, wait_for_string=prompt)

        cmd = "no boot system"
        self.ctx.send(cmd, wait_for_string=prompt)
        cmd = "boot system flash:" + pkg
        self.ctx.send(cmd, wait_for_string=prompt)

        self.ctx.send('end', wait_for_string=prompt)

        cmd = "write memory"
        install_activate_write_memory(self.ctx, cmd, self.ctx._connection.hostname)
        # self.ctx.send(cmd, timeout=300, wait_for_string=prompt)

        # Start activation

        install_activate_reload(self.ctx)

        self.ctx.info("Activate package done")

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)
        update_device_info_udi(self.ctx)

        # Verify the Image type

        output = self.ctx.send('show version | include ^System image')
        if pkg not in output:
            self.ctx.error('System image {} not found in show version: {}'.format(pkg, output))

        self.ctx.info('Activate image {} is successful'.format(pkg))
