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
from install import wait_for_prompt
from install import observe_install_add_remove
from install import send_admin_cmd
from csmpe.core_plugins.csm_get_inventory.exr.plugin import get_package, get_inventory


class Plugin(CSMPlugin):
    """This plugin removes inactive packages from the device."""
    name = "Install Remove Plugin"
    platforms = {'ASR9K', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Remove'}
    os = {'eXR'}
    
    def remove_id(self, pkg_id):
        cmd = "install remove id  {} ".format(pkg_id)
        self.ctx.info("Install remove with id {}".format(cmd))
        return cmd

    def remove(self, pkgs):
        cmd = "install remove  {} ".format(pkgs)
        self.ctx.info("Install remove with packages {}".format(cmd))
        return cmd

    def run(self):
        self.ctx.post_status("Install Remove Plugin")
        if hasattr(self.ctx, 'pkg_id'):
            pkg_id = " ".join(self.ctx.pkg_id)
            cmd = self.remove_id(pkg_id)
        else:
            packages = " ".join(self.ctx.software_packages)
            cmd = self.remove(packages)

        if self.ctx.shell == "Admin":
            self.ctx.send("admin", timeout=30)

        self.ctx.info("Remove Package(s) Pending")
        self.ctx.post_status("Remove Package(s) Pending")

        output = self.ctx.send(cmd, timeout=600)
        observe_install_add_remove(self.ctx, output)
        
        if self.ctx.shell == "Admin":
            self.ctx.info("Switching to admin mode")
            self.ctx.send("exit", timeout=30)
        self.ctx.info("Package(s) Removed Successfully")
        
        # Refresh package and inventory information
        #get_package(self.ctx)
        #get_inventory(self.ctx)
