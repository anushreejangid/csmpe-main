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
from condoor.exceptions import CommandSyntaxError


class Plugin(CSMPlugin):
    """This plugin captures custom commands and stores in the log directory."""
    name = "Custom Commands Capture Plugin"
    platforms = {'ASR9K', 'CRS', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'ASR900', 'N6K', 'IOS-XRv'}
    phases = {'Pre-Upgrade', 'Post-Upgrade', 'Migration-Audit', 'Pre-Migrate', 'Migrate', 'Post-Migrate'}

    def run(self):
        command_list = self.ctx.custom_commands
        if command_list:
            for cmd in command_list:
                self.ctx.info("Capturing output of '{}'".format(cmd))
                try:
                    output = self.ctx.send(cmd, timeout=2200)
                    file_name = self.ctx.save_to_file(cmd, output)
                    if file_name is None:
                        self.ctx.error("Unable to save '{}' output to file: {}".format(cmd, file_name))
                        return False
                except CommandSyntaxError:
                    self.ctx.error("Command Syntax Error: '" + cmd + "'")

        else:
            self.ctx.info("No custom commands provided.")
            return True
