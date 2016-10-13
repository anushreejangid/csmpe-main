# =============================================================================
# Copyright (c)  2016, Cisco Systems
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


def parse_show_platform(ctx, output):
    """
    :param ctx: PluginContext
    :param output: output from 'show platform'
    :return: dictionary of nodes

    Load for five secs: 1%/0%; one minute: 2%; five minutes: 2%
    No time source, *22:40:38.097 UTC Wed Oct 12 2016
    Chassis type: ASR-920-12CZ-A

    Slot      Type                State                 Insert time (ago)
    --------- ------------------- --------------------- -----------------
     0/0      12xGE-2x10GE-FIXED  ok                    03:07:10
    R0        ASR-920-12CZ-A      ok, active            03:09:23
    F0                            ok, active            03:09:23
    P0        ASR920-PSU0         ok                    never
    P1        ASR920-PSU1         ps, fail              never
    P2        ASR920-FAN          ok                    never

    Slot      CPLD Version        Firmware Version
    --------- ------------------- ---------------------------------------
    R0        1601191C            15.4(3r)S4
    F0        1601191C            15.4(3r)S4


    """

    ctx.info("IOS_XE in parse_show_platform")

    inventory = {}
    lines = output.split('\n')
    lines = [x for x in lines if x]
    slotcnt = 0
    for line in lines:
        line = line.strip()

        # ctx.info("line = {}".format(line))
        # ctx.info("len(line) = {}".format(len(line)))

        if len(line) > 0:

            states = re.split('\s+', line)
            # ctx.info("states[0] = {}".format(states[0]))

            if '--' in states[0]:
                continue

            if states[0] == 'Chassis':
                continue

            if states[0] == 'Slot':
                slotcnt += 1
                if slotcnt == 2:
                    break
                else:
                    continue

            if slotcnt == 1:
                node = line[0:8]
                node = node.strip()
                node_type = line[9:28]
                state = line[29:50]
                state = state.strip()
                config_state = line[51:60]
                config_state = config_state.strip()

                # ctx.info("node={}, type={}, state={}".format(node, node_type, state))

                entry = {
                    'type': node_type,
                    'state': state,
                    'config_state': config_state
                }
                inventory[node] = entry

    return inventory
