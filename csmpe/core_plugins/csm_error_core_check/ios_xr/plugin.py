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


class Plugin(CSMPlugin):
    """This plugin checks system logs against any errors, traceback of crash information."""
    name = "Core Error Check Plugin"
    platforms = {'ASR9K', 'CRS', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Post-Upgrade'}

    # matching any errors, core and traceback
    _string_to_check_re = re.compile(
        "^(.*(?:[Ee][Rr][Rr][Oo][Rr]|Core for pid|Traceback).*)$", re.MULTILINE
    )

    # TODO: Check log against
    # "Version of existing saved configuration detected to be incompatible with the installed software"
    # cfgmgr-rp[165]: %MGBL-CONFIG-4-VERSION : Version of existing saved configuration detected to be incompatible
    # with the installed software. Configuration will be restored from an alternate source and may take
    # longer than usual on this boot.

    def run(self):
        # FIXME: Consider optimization
        # The log may be large
        # Maybe better run sh logging | i "Error|error|ERROR|Traceback|Core for pid" directly on the device
        cmd = "show logging last 500"
        output = self.ctx.send(cmd, timeout=300)

        file_name = self.ctx.save_to_file(cmd, output)
        if file_name:
            self.ctx.info("Device log saved to {}".format(file_name))

        for match in re.finditer(self._string_to_check_re, output):
            self.ctx.warning(match.group())
