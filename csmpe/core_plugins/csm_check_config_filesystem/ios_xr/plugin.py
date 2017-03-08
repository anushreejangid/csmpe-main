# =============================================================================
# plugin
#
# Copyright (c)  2016, Cisco Systems
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


class Plugin(CSMPlugin):
    """This plugin checks the configuration filesystem"""
    name = "Config Filesystem Check Plugin"
    platforms = {'ASR9K', 'CRS', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Pre-Upgrade', "Pre-Activate", "Pre-Deactivate"}

    def run(self):
        """
        RP/0/RSP0/CPU0:R3#cfs check
        Tue May 17 09:56:43.720 UTC

        Creating any missing directories in Configuration File system...OK
        Initializing Configuration Version Manager...OK
        Syncing commit database with running configuration...OK
        """
        ok = 0
        message = []
        output = self.ctx.send("cfs check", timeout=300)
        lines = output.split("\n", 50)
        for line in lines:
            if line != "":
                message.append(line)
            if 'OK' in line:
                ok += 1

        for line in message:
            if ok < 3:
                self.ctx.warning(line)
            else:
                self.ctx.info(line)
        if ok < 3:
            self.ctx.error("The configuration filesystem has inconsistencies")
        else:
            self.ctx.info("Configuration filesystem is consistent")
