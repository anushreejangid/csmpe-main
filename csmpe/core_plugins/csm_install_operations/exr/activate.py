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
from install import install_activate_deactivate
from install import wait_for_prompt
from install import send_admin_cmd
from install import check_ncs6k_release, check_ncs4k_release
from csmpe.core_plugins.csm_get_inventory.exr.plugin import get_package, get_inventory
from csmpe.core_plugins.csm_install_operations.utils import update_device_info_udi


class Plugin(CSMPlugin):
    """This plugin Activates packages on the device."""
    name = "Install Activate Plugin"
    platforms = {'ASR9K', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Activate'}
    os = {'eXR'}

    def get_tobe_activated_pkg_list(self):
        """
        Produces a list of packaged to be activated
        """
        packages = self.ctx.software_packages

        pkgs = SoftwarePackage.from_package_list(packages)

        # RP/0/RP0/CPU0:Deploy#show install inactive
        # 5 inactive package(s) found:
        #     ncs6k-k9sec-5.2.5.47I
        #     ncs6k-mpls-5.2.5.47I
        #     ncs6k-5.2.5.47I.CSCuy47880-0.0.4.i
        #     ncs6k-mgbl-5.2.5.47I
        #     ncs6k-5.2.5.CSCuz65240-1.0.0

        admin_installed_inact = SoftwarePackage.from_show_cmd(send_admin_cmd(self.ctx, "show install inactive"))
        admin_installed_act = SoftwarePackage.from_show_cmd(send_admin_cmd(self.ctx, "show install active"))

        installed_inact = SoftwarePackage.from_show_cmd(self.ctx.send("show install inactive"))
        installed_act = SoftwarePackage.from_show_cmd(self.ctx.send("show install active"))

        installed_inact.update(admin_installed_inact)
        installed_act.update(admin_installed_act)

        # Packages to activate but not already active
        pkgs = pkgs - installed_act
        if pkgs:
            packages_to_activate = set()
            # After the packages are considered equal according to SoftwarePackage.__eq__(),
            # Use the package name in the inactive area.  It is possible that the package
            # name given for Activation may be an external filename like below.
            # ncs6k-5.2.5.CSCuz65240.smu to ncs6k-5.2.5.CSCuz65240-1.0.0
            for inactive_pkg in installed_inact:
                for pkg in pkgs:
                    if pkg == inactive_pkg:
                        packages_to_activate.add(inactive_pkg)

            if not packages_to_activate:
                to_deactivate = " ".join(map(str, pkgs))

                state_of_packages = "\nTo activate :{} \nInactive: {} \nActive: {}".format(
                    to_deactivate, installed_inact, installed_act
                )
                self.ctx.info(state_of_packages)
                self.ctx.error('To be activated packages not in inactive packages list.')
                return None
            else:
                if len(packages_to_activate) != len(packages):
                    self.ctx.info('Packages selected for activation: {}\n'.format(" ".join(map(str, packages))) +
                                  'Packages that are to be activated: {}'.format(" ".join(map(str,
                                                                                              packages_to_activate))))
                return " ".join(map(str, packages_to_activate))

    def run(self):
        """
        Performs install activate operation
        """
        check_ncs6k_release(self.ctx)
        check_ncs4k_release(self.ctx)
        self.ctx.post_status("Executing Install Activate plugin")

        packages = " ".join(self.ctx.software_packages)
        pkg_id = []
        
        if hasattr(self.ctx , 'pkg_id'):
            pkg_id = " ".join(self.ctx.pkg_id)

        if self.ctx.shell == "Admin":
            self.ctx.info("Switching to admin mode")
            self.ctx.send("admin", timeout=30)

        if pkg_id:
            if self.ctx.issu_mode:
                cmd = "install activate issu id {} ".format(pkg_id)
            else:
                cmd = "install activate id {} ".format(pkg_id)
        elif packages:
            if self.ctx.issu_mode:
                cmd = 'install activate issu {}'.format(packages)
            else:
                cmd = 'install activate {}'.format(packages)
        elif self.ctx.issu_mode:
            cmd = 'install activate issu'
        else:
            self.ctx.error("Unable to form xr command for activate")
            return
        self.ctx.info("Activate package(s) pending")
        self.ctx.post_status("Activate Package(s) Pending")
        self.ctx.info("[DEBUG]CMD: {}".format(cmd))

        install_activate_deactivate(self.ctx, cmd)
        if self.ctx.shell == "Admin":
            self.ctx.info("Switching to admin mode")
            self.ctx.send("exit", timeout=30)
            
        self.ctx.info("Activate package(s) done")
        self.ctx.info("Refreshing package and inventory information")
        self.ctx.post_status("Refreshing package and inventory information")
        # Refresh package and inventory information
        #get_package(self.ctx)
        #get_inventory(self.ctx)

        update_device_info_udi(self.ctx)
