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


import re

from csmpe.plugins import CSMPlugin
from install import watch_operation, log_install_errors
from csmpe.core_plugins.csm_get_inventory.exr.plugin import get_package, get_inventory


class Plugin(CSMPlugin):
    """This plugin commits packages on the device."""
    name = "Install Commit Plugin"
    platforms = {'ASR9K', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Commit'}
    os = {'eXR'}

    def run(self):
        """
        It performs commit operation
        RP/0/RP0/CPU0:Deploy#install commit
        May 27 16:34:04 Install operation 32 started by root:
          install commit
        May 27 16:34:05 Install operation will continue in the background

        RP/0/RP0/CPU0:Deploy#May 27 16:34:11 Install operation 32 finished successfully
        """
        cmd = "install commit"
        output = self.ctx.send(cmd)
        result = re.search('Install operation (\d+)', output)
        if result:
            op_id = result.group(1)
            watch_operation(self.ctx, op_id)
        else:
            log_install_errors(self.ctx, output)
            self.ctx.error("Operation ID not found.")
            return

        failed_oper = r'Install operation {} aborted'.format(op_id)
        success_oper = r'Install operation (\d+) finished successfully'

        # Not sure if this is still the message on NCS6K
        completed_with_failure = 'Install operation (\d+) completed with failure'

        cmd = "show install log {} detail".format(op_id)
        output = self.ctx.send(cmd)

        if re.search(failed_oper, output):
            log_install_errors(self.ctx, output)
            self.ctx.error("Install operation failed.")
            return

        if re.search(completed_with_failure, output):
            log_install_errors(self.ctx, output)
            self.ctx.info("Completed with failure but failure was after Point of No Return.")
        elif re.search(success_oper, output):
            self.ctx.info("Operation {} finished successfully.".format(op_id))

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)
