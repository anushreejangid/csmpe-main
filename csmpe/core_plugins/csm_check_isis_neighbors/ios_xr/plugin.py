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
from time import time
from datetime import datetime
from csmpe.plugins import CSMPlugin
from condoor.exceptions import CommandSyntaxError


class Plugin(CSMPlugin):
    """This plugin checks the ISIS neighbor."""
    name = "ISIS Neighbor Check Plugin"
    platforms = {'ASR9K', 'CRS', 'NCS1K', 'NCS4K', 'NCS5K', 'NCS5500', 'NCS6K', 'IOS-XRv'}
    phases = {'Pre-Upgrade', 'Post-Upgrade'}

    def run(self):
        """
        RP/0/RP0/CPU0:#show isis neighbor summary
        Thu May 19 18:06:11.239 UTC

        IS-IS isp neighbor summary:
        State         L1       L2     L1L2
        Up             0        0        1
        Init           0        0        0
        Failed         0        0        0

        This plugin check the number of ISIS Neighbors and store this information in format
        {
            <instance>: {
                "Up": [ <L1>, <L2>, <L1/L2> ],
                "Init": [ <L1>, <L2>, <L1/L2> ],
                "Failed": [ <L1>, <L2>, <L1/L2> ]
            }
        }
        """
        cmd = "show isis neighbor summary"
        isis_neighbor_info = {}
        try:
            output = self.ctx.send(cmd)
        except CommandSyntaxError:
            # This will happen when the device is ASR9K-64 and the ISIS package is not installed.
            self.ctx.info("The CLI 'show isis neighbor summary' is not available for checking the number " +
                          "of ISIS neighbors. Possible reason: the ISIS package (if any) needs to be installed.")
            return

        if output:
            isis_instance = None
            for line in output.split('\n'):
                result = re.search('IS-IS (.*) neighbor summary:', line)
                if result:
                    isis_instance = result.group(1)
                    isis_neighbor_info[isis_instance] = {}
                    continue
                result = re.search('Up\s+(\d+)\s+(\d+)\s+(\d+)', line)
                if result and isis_instance:
                    isis_neighbor_info[isis_instance]["Up"] = [result.group(n) for n in range(1, 4)]
                    continue
                result = re.search('Init\s+(\d+)\s+(\d+)\s+(\d+)', line)
                if result and isis_instance:
                    isis_neighbor_info[isis_instance]["Init"] = [result.group(n) for n in range(1, 4)]
                    continue
                result = re.search('Failed\s+(\d+)\s+(\d+)\s+(\d+)', line)
                if result and isis_instance:
                    isis_neighbor_info[isis_instance]["Failed"] = [result.group(n) for n in range(1, 4)]
                    continue

            if isis_instance:
                self.ctx.info("There is {} ISIS protocol instance(s) active".format(len(isis_neighbor_info)))
                for instance, state_dict in isis_neighbor_info.items():
                    for state, neighbors in state_dict.items():
                        self.ctx.info("Instance {} {:<6} L1={} L2={} L1L2={}".format(instance, state, *neighbors))

                filename = self.ctx.save_to_file(cmd, output)
                if filename:
                    self.ctx.info("The '{}' command output saved to {}".format(cmd, filename))

                if self.ctx.phase == "Pre-Upgrade":
                    self.ctx.save_data("isis_neighbors", isis_neighbor_info)
                    if filename:
                        # store the full_path to command output under the cmd key
                        self.ctx.save_data(cmd, filename)

            else:
                self.ctx.info("No ISIS protocol instance active")

            if self.ctx.phase == "Post-Upgrade":
                self.compare_data("isis_neighbors", isis_neighbor_info)

    def compare_data(self, storage_key, current_data):
        levels = ["L1", "L2", "L1L2"]
        previous_data, timestamp = self.ctx.load_data(storage_key)
        if previous_data is None:
            self.ctx.warning("No data stored from Pre-Upgrade phase. Can't compare.")
            return

        if previous_data:
            self.ctx.info("Pre-Upgrade phase data available for comparison")
            self.ctx.info("Pre-Upgrade data collected on {}".format(
                datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')))
            if timestamp < time() - (60 * 60 * 2):  # two hours
                self.ctx.warning("Pre-Upgrade phase data older than 2 hours")

            for previous_instance, previous_state_dict in previous_data.items():
                try:
                    current_state_dict = current_data[previous_instance]
                except KeyError:
                    self.ctx.warning("No ISIS instance '{}' detected after upgrade".format(previous_instance))
                    continue

                for state, previous_neighbors in previous_state_dict.items():
                    current_neighbors = current_state_dict[state]
                    if previous_neighbors != current_neighbors:
                        for level in range(3):
                            if previous_neighbors[level] != current_neighbors[level]:
                                self.ctx.warning(
                                    "Number of ISIS neighbors for instance '{}' in state {} at {} is different"
                                    "Pre-Install={} Post-Install={}".format(
                                        previous_instance, state, levels[level], previous_neighbors[level],
                                        current_neighbors[level]
                                    )
                                )
                else:
                    self.ctx.info("Number of ISIS neighbors for instance '{}' is the "
                                  "same as during pre-install check".format(previous_instance))
        else:
            self.ctx.warning("No data stored from Pre-Upgrade phase")
            return
