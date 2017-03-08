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
from install import observe_install_remove_all
from csmpe.core_plugins.csm_get_inventory.exr.plugin import get_package, get_inventory


class Plugin(CSMPlugin):
    """This plugin removes inactive packages from the device."""
    name = "Install Remove All Inactive Plugin"
    platforms = {'ASR9K', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Remove All Inactive'}
    os = {'eXR'}

    def run(self):

        cmd = 'install remove inactive all'

        self.ctx.info("Remove All Inactive Package(s) Pending")
        self.ctx.post_status("Remove All Inactive Package(s) Pending")

        observe_install_remove_all(self.ctx, cmd, self.ctx.prompt)

        self.ctx.info("Remove All Inactive Package(s) Successfully")

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)
