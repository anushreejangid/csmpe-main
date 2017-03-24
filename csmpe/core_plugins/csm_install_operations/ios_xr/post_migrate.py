# =============================================================================
# migrate_system.py - plugin for migrating classic XR to eXR/fleXR
#
# Copyright (c)  2013, Cisco Systems
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
import time

from csmpe.plugins import CSMPlugin
from migration_lib import wait_for_final_band, log_and_post_status, run_additional_custom_commands
from csmpe.core_plugins.csm_get_inventory.exr.plugin import get_package, get_inventory

TIMEOUT_FOR_COPY_CONFIG = 3600


class Plugin(CSMPlugin):
    """
    A plugin for loading configurations and upgrading FPD's
    after the system migrated to ASR9K IOS-XR 64 bit(eXR).
    If any FPD needs reloads after upgrade, the device
    will be reloaded after the upgrade.
    Console access is needed.
    """
    name = "Post-Migrate Plugin"
    platforms = {'ASR9K'}
    phases = {'Post-Migrate'}

    def _check_fpds_for_upgrade(self):
        """Check if any FPD's need upgrade, if so, upgrade all FPD's on all locations."""

        self.ctx.send("admin")

        fpdtable = self.ctx.send("show hw-module fpd")

        match = re.search("\d+/\w+.+\d+.\d+\s+[-\w]+\s+(NEED UPGD)", fpdtable)

        if match:
            total_num = len(re.findall("NEED UPGD", fpdtable)) + len(re.findall("CURRENT", fpdtable))
            if not self._upgrade_all_fpds(total_num):
                self.ctx.send("exit")
                self.ctx.error("FPD upgrade in eXR is not finished. Please check session.log.")
                return False
            else:
                return True

        self.ctx.send("exit")
        return True

    def _upgrade_all_fpds(self, num_fpds):
        """
        Upgrade all FPD's on all locations.
        If after all upgrade completes, some show that a reload is required to reflect the changes,
        the device will be reloaded.

        :param num_fpds: the number of FPD's that are in CURRENT and NEED UPGD states before upgrade.
        :return: True if upgraded successfully and reloaded(if necessary).
                 False if some FPD's did not upgrade successfully in 9600 seconds.
        """
        log_and_post_status(self.ctx, "Upgrading all FPD's.")
        self.ctx.send("upgrade hw-module location all fpd all")

        timeout = 9600
        poll_time = 30
        time_waited = 0

        time.sleep(60)
        while 1:
            # Wait till all FPDs finish upgrade
            time_waited += poll_time
            if time_waited >= timeout:
                break
            time.sleep(poll_time)
            output = self.ctx.send("show hw-module fpd")
            num_need_reload = len(re.findall("RLOAD REQ", output))
            if len(re.findall("CURRENT", output)) + num_need_reload >= num_fpds:
                if num_need_reload > 0:
                    log_and_post_status(self.ctx,
                                        "Finished upgrading FPD(s). Now reloading the device to complete the upgrade.")
                    self.ctx.send("exit")
                    return self._reload_all()
                self.ctx.send("exit")
                return True

        # Some FPDs didn't finish upgrade
        return False

    def _reload_all(self):
        """Reload the device with 1 hour maximum timeout"""
        self.ctx.reload(reload_timeout=3600, os=self.ctx.os_type)

        return self._wait_for_reload()

    def _wait_for_reload(self):
        """Wait for all nodes to come up with max timeout as 18 min"""
        # device.disconnect()
        # device.reconnect(max_timeout=300)
        log_and_post_status(self.ctx, "Waiting for all nodes to come to FINAL Band.")
        if wait_for_final_band(self.ctx):
            log_and_post_status(self.ctx, "All nodes are in FINAL Band.")
        else:
            log_and_post_status(self.ctx, "Warning: Not all nodes went to FINAL Band.")

        return True

    def run(self):

        log_and_post_status(self.ctx, "Waiting for all nodes to come to FINAL Band.")
        if not wait_for_final_band(self.ctx):
            self.ctx.warning("Warning: Not all nodes are in FINAL Band after 25 minutes.")

        log_and_post_status(self.ctx, "Capturing new IOS XR and Calvados configurations.")

        run_additional_custom_commands(self.ctx, {"show running-config", "admin show running-config"})

        self._check_fpds_for_upgrade()

        run_additional_custom_commands(self.ctx, {"show platform"})

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)
