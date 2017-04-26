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
    :param output: output from 'show platform'
    :return: dictionary of nodes

    Platform: ASR9K-X64
    Node              Type                       State             Config state
    --------------------------------------------------------------------------------
    0/RSP0/CPU0       A9K-RSP880-SE(Active)      IOS XR RUN        NSHUT
    0/RSP1/CPU0       A9K-RSP880-SE(Standby)     IOS XR RUN        NSHUT
    0/FT0             ASR-9904-FAN               OPERATIONAL       NSHUT
    0/0/CPU0          A9K-8X100GE-L-SE           IOS XR RUN        NSHUT
    0/PT0

    Platform: ASR9K-X64

    RP/0/RSP0/CPU0:vkg3#admin show platform
    Tue Apr 11 10:31:41.051 PST
    Node            Type                      State            Config State
    -----------------------------------------------------------------------------
    0/RSP0/CPU0     A9K-RSP880-SE(Active)     IOS XR RUN       PWR,NSHUT,MON
    0/RSP1/CPU0     A9K-RSP880-SE(Standby)    IOS XR RUN       PWR,NSHUT,MON
    0/FT0/SP        ASR-9904-FAN              READY
    0/0/CPU0        A9K-8X100GE-SE            IOS XR RUN       PWR,NSHUT,MON
    0/PS0/M0/SP     PWR-3KW-AC-V2             READY            PWR,NSHUT,MON
    0/PS0/M1/SP     PWR-3KW-AC-V2             READY            PWR,NSHUT,MON
    0/PS0/M2/SP     PWR-3KW-AC-V2             READY            PWR,NSHUT,MON
    0/PS0/M3/SP     PWR-3KW-AC-V2             READY            PWR,NSHUT,MON

    Platform: NCS6K
    RP/0/RP0/CPU0:ios#show platform

    Node              Type                       State             Config state
    --------------------------------------------------------------------------------
    0/0/CPU0          NC6-10X100G-M-K            IOS XR RUN        NSHUT
    0/0/NPU0          Slice                      UP
    0/0/NPU1          Slice                      UP
    0/0/NPU2          Slice                      UP
    0/0/NPU3          Slice                      UP
    0/0/NPU4          Slice                      UP
    0/5/CPU0          NC6-60X10GE-L-S            IOS XR RUN        NSHUT
    0/5/NPU0          Slice                      UP
    0/5/NPU1          Slice                      UP
    0/5/NPU2          Slice                      UP
    0/5/NPU3          Slice                      UP
    0/7/CPU0          NC6-20X100GE-M-C           IOS XR RUN        NSHUT
    0/7/NPU0          Slice                      UP
    0/7/NPU1          Slice                      UP
    0/7/NPU2          Slice                      UP
    0/7/NPU3          Slice                      UP
    0/7/NPU4          Slice                      UP
    0/RP0/CPU0        NC6-RP(Active)             IOS XR RUN        NSHUT
    0/RP1/CPU0        NC6-RP(Standby)            IOS XR RUN        NSHUT
    0/FC5             NC6-FC2-U                  OPERATIONAL       NSHUT
    0/CI0             NCS-CRFT                   OPERATIONAL       NSHUT
    0/FT0             NC6-FANTRAY-2              OPERATIONAL       NSHUT
    0/FT1             NC6-FANTRAY-2              OPERATIONAL       NSHUT
    0/PT0             NCS-AC-PWRTRAY             OPERATIONAL       NSHUT
    0/PT1             NCS-AC-PWRTRAY             OPERATIONAL       NSHUT
    0/PT2             NCS-AC-PWRTRAY             OPERATIONAL       NSHUT
    0/PT3             NCS-AC-PWRTRAY             OPERATIONAL       NSHUT
    0/PT4             NCS-AC-PWRTRAY             OPERATIONAL       NSHUT
    0/PT5             NCS-AC-PWRTRAY             OPERATIONAL       NSHUT

    Platform: NCS5500
    RP/0/RP0/CPU0:att-1#show platform

    Node              Type                       State             Config state
    --------------------------------------------------------------------------------
    0/1/CPU0          NC55-24X100G-SE            IOS XR RUN        NSHUT
    0/1/NPU0          Slice                      UP
    0/1/NPU1          Slice                      UP
    0/1/NPU2          Slice                      UP
    0/1/NPU3          Slice                      UP
    0/RP0/CPU0        NC55-RP(Active)            IOS XR RUN        NSHUT
    0/RP1/CPU0        NC55-RP(Standby)           IOS XR RUN        NSHUT
    0/FC1             UNKNOWN                    UNKNOWN
    0/FC5             NC55-5508-FC               OPERATIONAL       NSHUT
    0/FT0             NC55-5508-FAN              OPERATIONAL       NSHUT
    0/FT2             NC55-5508-FAN              OPERATIONAL       NSHUT
    0/SC0             UNKNOWN                    UNKNOWN
    0/SC1             NC55-SC                    OPERATIONAL       NSHUT

    Platform: NCS5K
    RP/0/RP0/CPU0:montreal#show platform


    Node              Type                       State             Config state

    --------------------------------------------------------------------------------

    0/RP0/CPU0        NCS-5001(Active)           IOS XR RUN        NSHUT

    0/FT0             NCS-5001-FN-BK             OPERATIONAL       NSHUT

    0/FT1             NCS-5001-FN-BK             OPERATIONAL       NSHUT

    Platform: NCS4K
    RP/0/RP0:DC2-4K#show platform

    Node              Type                       State             Config state
    --------------------------------------------------------------------------------
    0/0/CPU0          NCS4K-2H-W                 IOS XR RUN        NSHUT
    0/1/CPU0          NCS4K-2H10T-OP-KS          IOS XR RUN        NSHUT
    0/4/CPU0          NCS4K-2H-O-K               IOS XR RUN        NSHUT
    0/5/CPU0          NCS4K-24LR-O-S             IOS XR RUN        NSHUT
    0/10/CPU0         NCS4K-20T-O-S              IOS XR RUN        NSHUT
    0/11/CPU0         NCS4K-2H-O-K               IOS XR RUN        NSHUT
    0/13/CPU0         NCS4K-2H-O-K               IOS XR RUN        NSHUT
    0/15/CPU0         NCS4K-24LR-O-S             POWERED_OFF       NSHUT
    0/RP0/CPU0        NCS4K-RP                   IOS XR RUN        NSHUT
    0/RP1/CPU0        NCS4K-RP                   IOS XR RUN        NSHUT
    0/FC0             NCS4016-FC2-M              OPERATIONAL       NSHUT
    0/FC1             NCS4016-FC2-M              OPERATIONAL       NSHUT
    0/FC2             NCS4016-FC2-M              OPERATIONAL       NSHUT
    0/FC3             NCS4016-FC2-M              OPERATIONAL       NSHUT
    0/CI0             NCS4K-CRAFT                OPERATIONAL       NSHUT
    0/FT0             NCS4K-FTA                  OPERATIONAL       NSHUT
    0/FT1             NCS4K-FTA                  OPERATIONAL       NSHUT
    0/PT0             NCS4K-DC-PEM               OPERATIONAL       NSHUT
    0/PT1             NCS4K-DC-PEM               OPERATIONAL       NSHUT
    0/EC0             NCS4K-ECU                  OPERATIONAL       NSHUT

    Platform NCS1K:
    RP/0/RP0/CPU0:ios#show platform

    Node              Type                       State             Config state
    --------------------------------------------------------------------------------
    0/RP0/CPU0        NCS1K-CNTLR(Active)        IOS XR RUN        NSHUT

    Platform: XRv9K
    RP/0/RP0/CPU0:XRv9K#show platform
    Tue Apr 11 23:55:51.866 UTC
    Node              Type                       State             Config state
    --------------------------------------------------------------------------------
    0/RP0/CPU0        R-IOSXRV9000-RP(Active)    IOS XR RUN        NSHUT
    """
    inventory = {}
    sl = ['node', 'type', 'state', 'config state']
    dl = {}

    lines = output.split('\n')
    lines = [x for x in lines if x]
    for line in lines:
        line = line.strip()

        if line[0:4] == 'Node':
            line = line.lower()
            for s in sl:
                n = line.find(s)
                if n != -1:
                    dl[str(s)] = n
                else:
                    ctx.warning("unrecognized show platform header {}".format(line))
                    return None

        if line[0].isdigit():
            node = line[:dl["type"]]
            if not re.search('CPU\d+\s*$', node):
                continue

            node_type = line[dl['type']:dl['state']].strip()
            state = line[dl['state']:dl['config state']].strip()
            config_state = line[dl['config state']:].strip()

            entry = {
                'type': node_type,
                'state': state,
                'config_state': config_state
            }
            inventory[node] = entry

    return inventory
