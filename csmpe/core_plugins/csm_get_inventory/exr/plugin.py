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

import time
from csmpe.plugins import CSMPlugin


class Plugin(CSMPlugin):
    """This plugin retrieves software information from the device."""
    name = "Get Inventory Plugin"
    platforms = {'ASR9K', 'NCS1K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Get-Inventory'}
    os = {'eXR'}

    def run(self):
        get_package(self.ctx)
        get_inventory(self.ctx)


def get_inventory(ctx):
    # Save the output of "show inventory" in admin mode
    output = get_output_in_admin_mode(ctx, "show inventory")
    ctx.save_data("cli_show_inventory", output)


def get_package(ctx):
    """
    Convenient method, it may be called by outside of the plugin
    """

    # Get the admin packages
    ctx.save_data("cli_admin_show_install_inactive",
                  get_output_in_admin_mode(ctx, "show install inactive"))
    ctx.save_data("cli_admin_show_install_active",
                  get_output_in_admin_mode(ctx, "show install active"))
    ctx.save_data("cli_admin_show_install_committed",
                  get_output_in_admin_mode(ctx, "show install committed"))

    # Get the non-admin packages
    ctx.save_data("cli_show_install_inactive",
                  get_output_in_admin_mode(ctx, "show install inactive", admin=False))
    ctx.save_data("cli_show_install_active",
                  get_output_in_admin_mode(ctx, "show install active", admin=False))
    ctx.save_data("cli_show_install_committed",
                  get_output_in_admin_mode(ctx, "show install committed", admin=False))


def get_output_in_admin_mode(ctx, cmd, admin=True):
    """
    :param ctx:
    :param cmd:
    :param admin: True - Calvados, False - xr
    :return: cmd ouput

    Polling as a workaround when the router cmd is not ready:

    RP/0/RP0/CPU0:xrg-ncs-2#show install active
    Node 0/0/CPU0
    Node unresponsive (possible ongoing install operation).
    Please try command later

    Node 0/2/CPU0
    Node unresponsive (possible ongoing install operation).
    Please try command later
    """

    if admin:
        command = 'admin ' + cmd
        ctx.send("admin")
    else:
        command = cmd

    x = 0
    output = ctx.send(cmd)
    while x < 60:
        if 'Please try command later' in output:
            x += 1
            time.sleep(10)
            output = ctx.send(cmd)
        else:
            break

    if admin:
        ctx.send("exit")

    if 'Please try command later' in output:
        ctx.warning('The command {} is not ready after 10 minutes. Please manually '
                    'retrieve latest software from the Host Dashboard'.format(command))

    return output
