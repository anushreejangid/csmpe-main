# =============================================================================
# hardware_audit.py - plugin for auditing hardware for migrating classic XR to eXR/fleXR
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
import json

from csmpe.plugins import CSMPlugin
from migration_lib import SUPPORTED_HW_JSON, log_and_post_status, parse_admin_show_platform
from csmpe.core_plugins.csm_get_inventory.ios_xr.plugin import get_package, get_inventory


class Plugin(CSMPlugin):
    """
    A plugin for auditing hardware for migration from
    ASR9K IOS-XR (a.k.a. XR) to ASR9K IOS-XR 64 bit (a.k.a. eXR)

    Console access is needed.
    """
    name = "Migration Audit Plugin"
    platforms = {'ASR9K'}
    phases = {'Migration-Audit'}

    rp_pattern = re.compile('\d+/RS??P\d+/CPU\d+')
    fc_pattern = re.compile('\d+/FC\d+/SP')
    fan_pattern = re.compile('\d+/FT\d+/SP')
    pem_pattern = re.compile('\d+/P[SM]\d+/M?\d+/SP')
    lc_pattern = re.compile('\d+/\d+/CPU\d+')

    def _check_if_hw_supported_and_in_valid_state(self, inventory, supported_hw, override):
        """
        Check if RSP/RP/FAN/PEM/FC/LC/MPA currently on device are supported and are in valid state for migration.

        Minimal requirements (with override=True):
                            all RSP/RP's are supported and in IOS XR RUN state
                            all FC's are supported and in OK state
                            all supported FAN/PEM's are in READY state
                            all supported LC's are in IOS XR RUN state
                            all MPA's are supported and in OK state

        default requirements (with override=False):
                            all RSP/RP's are supported and in IOS XR RUN state
                            all FC's are supported and in OK state
                            all FAN/PEM's are supported and in READY state
                            all supported LC's are in IOS XR RUN state
                            all MPA's are supported and in OK state

        :param inventory: the result for parsing the output of 'admin show platform'
        :param supported_hw: stores info about which card types are supported in eXR for RSP/RP/FAN/PEM/FC/LC
        :param override: override the requirement to check FAN/PEM hardware types
        :return: Errors out if a requirement is not met.
                If all requirements are met, returns a dictionary used later in other plugin(s) for monitoring
                the success of FPD upgrade. Keys are node names parsed from 'admin show platform'.
                 Values are integers. Value can either be 0 or 1. value 1 means that this node is supported in
                 eXR and is in valid state for migration. value 0 means that either this node is a PEM/FAN, or
                 this node is not supported in eXR.
        """
        fpd_relevant_nodes = {}

        for i in xrange(0, len(inventory)):
            node, entry = inventory[i]

            if node in fpd_relevant_nodes:
                continue

            if self.rp_pattern.match(node):
                rp_or_rsp = self._check_if_supported_and_in_valid_state(node, entry,
                                                                        supported_hw.get("RP"), "IOS XR RUN")

                fpd_relevant_nodes[node] = rp_or_rsp

            elif self.fc_pattern.match(node):

                fc = self._check_if_supported_and_in_valid_state(node, entry,
                                                                 supported_hw.get("FC"), "OK")
                fpd_relevant_nodes[node] = fc

            elif self.lc_pattern.match(node):

                lc = self._check_if_supported_and_in_valid_state(node, entry, supported_hw.get("LC"),
                                                                 "IOS XR RUN", mandatory=False)
                for j in xrange(i + 1, len(inventory)):
                    next_node, next_entry = inventory[j]
                    if "MPA" in next_entry["type"]:
                        mpa = self._check_if_supported_and_in_valid_state(next_node, next_entry,
                                                                          supported_hw.get("MPA"), "OK")
                        fpd_relevant_nodes[next_node] = mpa

                fpd_relevant_nodes[node] = lc

            elif self.fan_pattern.match(node):
                self._check_if_supported_and_in_valid_state(node, entry,
                                                            supported_hw.get("FAN"),
                                                            "READY", mandatory=not override)
                fpd_relevant_nodes[node] = 0
            elif self.pem_pattern.match(node):
                    self._check_if_supported_and_in_valid_state(node, entry,
                                                                supported_hw.get("PEM"),
                                                                "READY", mandatory=not override)
                    fpd_relevant_nodes[node] = 0
            else:
                fpd_relevant_nodes[node] = 1

        return fpd_relevant_nodes

    def _check_if_supported_and_in_valid_state(self, node_name, value,
                                               supported_type_list, operational_state, mandatory=True):
        """
        Check if a card (RSP/RP/FAN/PEM/FC/MPA) is supported and in valid state.
        :param node_name: the name under "Node" column in output of CLI "show platform". i.e., "0/RSP0/CPU0"
        :param value: the inventory value for nodes - through parsing output of "show platform"
        :param supported_type_list: the list of card types/pids that are supported for migration
        :param operational_state: the state that this node can be in in order to qualify for migration
        :param mandatory: if mandatory is True, if this node matches the card_pattern, it must be supported card
                          type in order to qualify for migration. If it's False, it's not necessary that the card
                          type is supported, but if it is supported, its state must be in the operational state
        :return: 1 if it's confirmed that the node is supported and in the operational state for migration.

                 0 if it's not mandatory that this node has supported card type, and it's confirmed that it does
                    not have supported card type, but it is in the operational state for migration.

                 errors out if this node is in either of the situations below:
                    1. It is mandatory for this node to have supported card type, but the card type of this node is NOT
                        supported for migration.
                    2. This node is supported for migration, but it is not in the operational state for migration.
        """
        supported = False
        if supported_type_list is None:
            self.ctx.error("The supported hardware list is missing information.")
        for supported_type in supported_type_list:
            if supported_type in value['type']:
                supported = True
                break
        if mandatory and not supported:
            self.ctx.error("The card type for {} is not supported for migration to ASR9K-64.".format(node_name) +
                           " Please check the user manual under 'Help' on CSM Server for list of " +
                           "supported hardware for ASR9K-64.")

        if supported and value['state'] != operational_state:
            self.ctx.error("{} is supported in ASR9K-64, but it's in {}".format(node_name, value['state']) +
                           " state. Valid operational state for migration: {}".format(operational_state))
        if supported:
            return 1
        return 0

    def run(self):

        software_version_tuple = self.ctx.load_job_data('hardware_audit_version')
        if software_version_tuple:
            software_version = software_version_tuple[0]
            self.ctx.info("Hardware audit for software release version " + str(software_version))
        else:
            self.ctx.error("No software version selected.")

        override_hw_req_tuple = self.ctx.load_job_data('override_hw_req')
        if override_hw_req_tuple and override_hw_req_tuple[0] == "1":
            override_hw_req = True
            log_and_post_status(self.ctx,
                                "Running hardware audit to check minimal requirements for card types and states.")
        else:
            override_hw_req = False
            log_and_post_status(self.ctx, "Running hardware audit on all nodes.")

        with open(SUPPORTED_HW_JSON) as supported_hw_file:
            supported_hw = json.load(supported_hw_file)

        if not supported_hw.get(software_version):
            self.ctx.error("No hardware support information available for release {}.".format(software_version))

        output = self.ctx.send("admin show platform")
        inventory = parse_admin_show_platform(output)

        log_and_post_status(self.ctx, "Check if cards on device are supported for migration.")
        fpd_relevant_nodes = self._check_if_hw_supported_and_in_valid_state(inventory,
                                                                            supported_hw[software_version],
                                                                            override_hw_req)
        self.ctx.save_job_data("fpd_relevant_nodes", fpd_relevant_nodes)

        log_and_post_status(self.ctx, "Hardware audit completed successfully.")

        # Refresh package and inventory information
        get_package(self.ctx)
        get_inventory(self.ctx)

        return True
