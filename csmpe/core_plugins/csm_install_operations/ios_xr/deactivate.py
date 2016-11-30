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

from package_lib import SoftwarePackage
from csmpe.plugins import CSMPlugin
from install import install_activate_deactivate
from csmpe.core_plugins.csm_get_inventory.ios_xr.plugin import get_package, get_inventory


class Plugin(CSMPlugin):
    """This plugin deactivates packages on the device."""
    name = "Install Deactivate Plugin"
    platforms = {'ASR9K', 'CRS'}
    phases = {'Deactivate'}
    os = {'XR'}

    def get_tobe_deactivated_pkg_list(self):
        """
        Produces a list of packaged to be deactivated
        """
        packages = self.ctx.software_packages
        pkgs = SoftwarePackage.from_package_list(packages)

        installed_act = SoftwarePackage.from_show_cmd(self.ctx.send("admin show install active summary"))

        if pkgs:
            # packages to be deactivated must be active packages
            packages_to_deactivate = pkgs & installed_act
            if not packages_to_deactivate:
                to_deactivate = " ".join(map(str, pkgs))

                state_of_packages = "\nTo deactivate :{} \nActive: {}".format(
                    to_deactivate, installed_act
                )

                self.ctx.info(state_of_packages)
                self.ctx.error('To be deactivated packages not in inactive packages list.')
                return None
            else:
                if len(packages_to_deactivate) != len(packages):
                    self.ctx.info('Packages selected for deactivation: {}\n'.format(" ".join(map(str, packages))) +
                                  'Packages that are to be deactivated: {}'.format(" ".join(map(str,
                                                                                            packages_to_deactivate))))
                return " ".join(map(str, packages_to_deactivate))

    def run(self):
        """
        Performs install deactivate operation
        """
        operation_id = None
        if hasattr(self.ctx, 'operation_id'):
            if self.ctx.operation_id != -1:
                self.ctx.info("Using the operation ID: {}".format(self.ctx.operation_id))
                operation_id = self.ctx.operation_id

        if operation_id is None or operation_id == -1:
            tobe_deactivated = self.get_tobe_deactivated_pkg_list()
            if not tobe_deactivated:
                self.ctx.info("Nothing to be deactivated.")
                return True

        if operation_id is not None and operation_id != -1:
            cmd = 'admin install deactivate id {} prompt-level none async'.format(operation_id)
        else:
            cmd = 'admin install deactivate {} prompt-level none async'.format(tobe_deactivated)

        self.ctx.info("Deactivate package(s) pending")
        self.ctx.post_status("Deactivate Package(s) Pending")

        install_activate_deactivate(self.ctx, cmd)

        self.ctx.info("Deactivate package(s) done")

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)
