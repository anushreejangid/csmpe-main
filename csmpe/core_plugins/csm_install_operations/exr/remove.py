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

from package_lib import SoftwarePackage
from csmpe.plugins import CSMPlugin
from install import observe_install_add_remove
from install import send_admin_cmd
from csmpe.core_plugins.csm_get_inventory.exr.plugin import get_package, get_inventory


class Plugin(CSMPlugin):
    """This plugin removes inactive packages from the device."""
    name = "Install Remove Plugin"
    platforms = {'ASR9K', 'NCS1K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv', 'NCS4K'}
    phases = {'Remove'}
    os = {'eXR'}

    def run(self):
        packages = self.ctx.software_packages
        if packages is None:
            self.ctx.error("No package list provided")
            return

        pkgs = SoftwarePackage.from_package_list(packages)

        admin_installed_inact = SoftwarePackage.from_show_cmd(send_admin_cmd(self.ctx, "show install inactive"))
        installed_inact = SoftwarePackage.from_show_cmd(self.ctx.send("show install inactive"))

        installed_inact.update(admin_installed_inact)
        packages_to_remove = pkgs & installed_inact

        if not packages_to_remove:
            self.ctx.warning("Packages already removed. Nothing to be removed")
            return

        to_remove = " ".join(map(str, packages_to_remove))

        cmd = 'install remove {}'.format(to_remove)

        self.ctx.info("Remove Package(s) Pending")
        self.ctx.post_status("Remove Package(s) Pending")

        output = self.ctx.send(cmd, timeout=600)
        observe_install_add_remove(self.ctx, output)

        self.ctx.info("Package(s) Removed Successfully")

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)
