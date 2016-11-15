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

from csmpe.plugins import CSMPlugin
from csmpe.core_plugins.csm_get_inventory.ios.plugin import get_package, get_inventory
from install import remove_exist_image


class Plugin(CSMPlugin):
    """This plugin removes inactive packages from the device."""
    name = "Install Remove Plugin"
    platforms = {'ASR900'}
    phases = {'Remove'}
    os = {'IOS'}

    def run(self):
        packages_to_remove = self.ctx.software_packages
        if packages_to_remove is None:
            self.ctx.error("No package list provided")
            return

        self.ctx.info("Remove Package(s) Pending")
        self.ctx.post_status("Remove Package(s) Pending")

        for pkg in packages_to_remove:
            self.ctx.info("Delete package flash:{}".format(pkg))

            package = 'flash:' + pkg
            output = remove_exist_image(self.ctx, package)

            if not output:
                self.ctx.info("flash:{} Removal Failed".format(pkg))
                break
        else:
            self.ctx.info("Package(s) Removed Successfully")
            # Refresh package and inventory information
            get_package(self.ctx)
            get_inventory(self.ctx)
            return

        self.ctx.error("Package(s) Removal Failed")
        return
