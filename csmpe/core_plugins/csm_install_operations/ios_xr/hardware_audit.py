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
from migration_lib import SUPPORTED_HW_JSON, log_and_post_status
from csmpe.core_plugins.csm_node_status_check.ios_xr.plugin_lib import parse_show_platform


ROUTEPROCESSOR_RE = '\d+/RS??P\d+/CPU\d+'
LINECARD_RE = '\d+/\d+/CPU\d+'
FAN = '\d+/FT\d+/SP'
PEM = '\d+/P[SM]\d+/M?\d+/SP'
FC = '\d+/FC\d+/SP'

VALID_STATE = ['IOS XR RUN',
               'PRESENT',
               'READY',
               'OK']


class Plugin(CSMPlugin):
    """
    A plugin for auditing hardware for migration from
    ASR9K IOS-XR (a.k.a. XR) to ASR9K IOS-XR 64 bit (a.k.a. eXR)

    Console access is needed.
    """
    name = "Migration Audit Plugin"
    platforms = {'ASR9K'}
    phases = {'Migration-Audit'}

    def _check_if_hw_supported_and_in_valid_state(self, inventory, supported_hw, override):
        """
        Check if RSP/RP/FAN/PEM/FC/LC currently on device are supported and are in valid state for migration.

        Minimal requirements (with override=True):
                            all RSP/RP's are supported and in IOS XR RUN state
                            all FC's are supported and in OK state
                            all supported FAN/PEM's are in READY state
                            all supported LC's are in IOS XR RUN state

        default requirements (with override=False):
                            all RSP/RP's are supported and in IOS XR RUN state
                            all FC's are supported and in OK state
                            all FAN/PEM's are supported and in READY state
                            all supported LC's are in IOS XR RUN state

        :param inventory: the result for parsing the output of 'admin show platform'
        :param supported_hw: stores info about which card types are supported in eXR for RSP/RP/FAN/PEM/FC/LC
        :param override: override the requirement to check FAN/PEM hardware types
        :return: if requirements are met, returns a list of node names containing all RSP's, RP's and supported LC's
                that are in IOS XR RUN state and all FC's that are in OK state. This list is used for upgrading fpd's
                 and checking the success of fpd upgrade. Errors out otherwise.
        """

        rp_pattern = re.compile(ROUTEPROCESSOR_RE)
        fc_pattern = re.compile(FC)
        fan_pattern = re.compile(FAN)
        pem_pattern = re.compile(PEM)
        lc_pattern = re.compile(LINECARD_RE)

        fpd_relevant_nodes = []

        for key, value in inventory.items():

            rp_or_rsp = self._check_if_supported_and_in_valid_state(key, rp_pattern, value,
                                                                    supported_hw.get("RP"), "IOS XR RUN")
            if rp_or_rsp == 1:
                fpd_relevant_nodes.append(key)
            elif not rp_or_rsp:

                fc = self._check_if_supported_and_in_valid_state(key, fc_pattern, value,
                                                                 supported_hw.get("FC"), "OK")
                if fc == 1:
                    fpd_relevant_nodes.append(key)
                elif not fc:

                    lc = self._check_if_supported_and_in_valid_state(key, lc_pattern, value, supported_hw.get("LC"),
                                                                     "IOS XR RUN", mandatory=False)
                    if lc == 1:
                        fpd_relevant_nodes.append(key)
                    elif not lc:
                        fan = self._check_if_supported_and_in_valid_state(key, fan_pattern, value,
                                                                          supported_hw.get("FAN"),
                                                                          "READY", mandatory=not override)
                        if not fan:
                            self._check_if_supported_and_in_valid_state(key, pem_pattern, value,
                                                                        supported_hw.get("PEM"),
                                                                        "READY", mandatory=not override)
        return fpd_relevant_nodes

    def _check_if_supported_and_in_valid_state(self, node_name, card_pattern, value,
                                               supported_type_list, operational_state, mandatory=True):
        """
        Check if a card (RSP/RP/FAN/PEM/FC) is supported and in valid state.
        :param node_name: the name under "Node" column in output of CLI "show platform". i.e., "0/RSP0/CPU0"
        :param card_pattern: the regex for either the node name of a RSP, RP, FAN, PEM or FC
        :param value: the inventory value for nodes - through parsing output of "show platform"
        :param supported_type_list: the list of card types/pids that are supported for migration
        :param operational_state: the state that this node can be in in order to qualify for migration
        :param mandatory: if mandatory is True, if this node matches the card_pattern, it must be supported card
                          type in order to qualify for migration. If it's False, it's not necessary that the card
                          type is supported, but if it is supported, its state must be in the operational state
        :return: 1 if this node is indeed the asked card(RP/RSP/FAN/PEM/FC/LC) and it's confirmed that it's supported
                    and in the operational state for migration.

                 -1 if this node is indeed the asked card(RP/RSP/FAN/PEM/FC/LC), it's not mandatory that this node has
                    supported card type, and it's confirmed that it does not have supported card type, but it is in
                    the operational state for migration.

                 0 if this node is not the asked card(RP/RSP/FAN/PEM/FC/LC).

                 errors out if this node is indeed the asked card(RP/RSP/FAN/PEM/FC) and it's either of the situations
                    below:
                    1. It is mandatory for this node to have supported card type, but the card type of this node is NOT
                        supported for migration.
                    2. This node is supported for migration, but it is not in the operational state for migration.
        """
        if card_pattern.match(node_name):
            supported = False
            if not supported_type_list:
                self.ctx.error("The supported hardware list is missing information.")
            for supported_type in supported_type_list:
                if supported_type in value['type']:
                    supported = True
                    break
            if mandatory and not supported:
                self.ctx.error("The card type for {} is not supported for migration to ASR9K-X64.".format(node_name) +
                               " Please check the user manual under 'Help' on CSM Server for list of " +
                               "supported hardware for ASR9K-X64.")

            if supported and value['state'] != operational_state:
                self.ctx.error("{}={}: Not in valid operational state for migration. ".format(node_name, value) +
                               "Operational state: {}", operational_state)
            if supported:
                return 1
            else:
                return -1
        return 0

    def run(self):

        try:
            software_version = self.ctx.hardware_audit_software_version
            print "software_version = " + str(software_version)
            self.ctx.info("Hardware audit for software release version " + str(software_version))
        except AttributeError:
            if self.ctx.load_data('software_version'):
                software_version = self.ctx.load_data('software_version')[0]
                self.ctx.info("Hardware audit for software release version " + str(software_version))
            else:
                self.ctx.error("No software version selected.")

        try:
            override_hw_req = self.ctx.pre_migrate_override_hw_req
        except AttributeError:
            override_hw_req = False

        if override_hw_req:
            log_and_post_status(self.ctx,
                                "Running hardware audit to check minimal requirements for card types and states.")
        else:
            log_and_post_status(self.ctx, "Running hardware audit on all nodes.")

        with open(SUPPORTED_HW_JSON) as supported_hw_file:
            supported_hw = json.load(supported_hw_file)

        if not supported_hw.get(software_version):
            self.ctx.error("No hardware support information available for release {}.".format(software_version))

        output = self.ctx.send("admin show platform")
        inventory = parse_show_platform(self.ctx, output)

        log_and_post_status(self.ctx, "Check if cards on device are supported for migration.")
        fpd_relevant_nodes = self._check_if_hw_supported_and_in_valid_state(inventory,
                                                                            supported_hw[software_version],
                                                                            override_hw_req)
        self.ctx.save_data("fpd_relevant_nodes", fpd_relevant_nodes)

        return True
