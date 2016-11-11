# =============================================================================
# CSMPluginManager
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

import pkginfo
from condoor import ConnectionError
from stevedore.dispatch import DispatchExtensionManager
from stevedore.exception import NoMatches

from context import PluginContext, condoor_ng

install_phases = ['Pre-Upgrade', 'Pre-Add', 'Add', 'Pre-Activate', 'Activate', 'Pre-Deactivate',
                  'Deactivate', 'Pre-Remove', 'Remove', 'Commit', 'Get-Inventory',
                  'Hardware-Audit', 'Pre-Migrate', 'Migrate', 'Post-Migrate', 'Post-Upgrade', 'FPD-Upgrade']

auto_pre_phases = ["Add", "Activate", "Deactivate"]


class CSMPluginManager(object):

    def __init__(self, ctx=None, invoke_on_load=True):
        self._ctx = PluginContext(ctx)
        # The context contains device information after discovery phase
        # There is no need to load plugins which does not match the family and os
        try:
            self._platform = self._ctx.family
        except AttributeError:
            self._platform = None
        try:
            self._os = self._ctx.os_type
        except AttributeError:
            self._os = None

        self._phase = None
        self._name = None

        self.load(invoke_on_load=invoke_on_load)

    def load(self, invoke_on_load=True):
        self._manager = DispatchExtensionManager(
            "csm.plugin",
            self._check_plugin,
            invoke_on_load=invoke_on_load,
            invoke_args=(self._ctx,),
            propagate_map_exceptions=True,
            on_load_failure_callback=self._on_load_failure,
        )
        self._build_plugin_list()

    def __getitem__(self, item):
        return self._manager.__getitem__(item)

    def _build_plugin_list(self):
        self.plugins = {}
        for ext in self._manager:
            self.plugins[ext.name] = {
                #  'package_name': ext.entry_point.dist.project_name,
                'package_name': ext.entry_point.module_name.split(".")[0],
                'name': ext.plugin.name,
                'description': ext.plugin.__doc__,
                'phases': ext.plugin.phases,
                'platforms': ext.plugin.platforms,
                'os': ext.plugin.os
            }

    def _filter_func(self, ext, *args, **kwargs):
        if self._platform and self._platform not in ext.plugin.platforms:
            return False
        if self._phase and self._phase not in ext.plugin.phases:
            return False
        if self._name and ext.plugin.name not in self._name:
            return False
        # if detected os is set and plugin os set is not empty and detected os is not in plugin os then
        # plugin does not match
        if self._os and bool(ext.plugin.os) and self._os not in ext.plugin.os:
            return False
        return True

    def _dispatch(self, ext, *args, **kwargs):
        if self._filter_func(ext):
            self._ctx.current_plugin = None
            self._ctx.info("Dispatching: '{}'".format(ext.plugin.name))
            self._ctx.post_status(ext.plugin.name)
            self._ctx.current_plugin = ext.plugin.name
            return True
        return False

    def _on_load_failure(self, manager, entry_point, exc):
        self._ctx.warning("Plugin load error: {}".format(entry_point))
        self._ctx.warning("Exception: {}".format(exc))

    def _check_plugin(self, ext, *args, **kwargs):
        attributes = ['name', 'phases', 'platforms', 'os']
        plugin = ext.plugin
        for attribute in attributes:
            if not hasattr(plugin, attribute):
                self._ctx.warning("Attribute '{}' missing in plugin class: {}".format(
                    attribute, ext.entry_point.module_name))
                return False
        return self._filter_func(ext)

    def get_package_metadata(self, name):
        try:
            meta = pkginfo.Installed(name)
        except ValueError as e:
            print(e)
            return None
        return meta

    def _get_package_names(self):
        return self.get_package_metadata().keys()

    def dispatch(self, func):
        if not condoor_ng:
            try:
                self._ctx.connect()
            except ConnectionError as e:
                self._ctx.post_status(e.message)
                self._ctx.error(e.message)
                return False

        results = []
        current_phase = self._ctx.phase
        if self._ctx.phase in auto_pre_phases:
            phase = "Pre-{}".format(self._ctx.phase)
            self.set_phase_filter(phase)
            self._ctx.info("Phase: {}".format(self._phase))
            try:
                results = self._manager.map_method(self._dispatch, func)
            except NoMatches:
                self._ctx.warning("No {} plugins found".format(phase))
            self._ctx.current_plugin = None

        self.set_phase_filter(current_phase)
        self._ctx.info("Phase: {}".format(self._phase))
        try:
            results += self._manager.map_method(self._dispatch, func)
        except NoMatches:
            self._ctx.post_status("No plugins found for phase {}".format(self._phase))
            self._ctx.error("No plugins found for phase {}".format(self._phase))

        self._ctx.current_plugin = None
        self._ctx.success = True
        self._ctx.info("CSM Plugin Manager Finished")
        self._ctx.disconnect()
        return results

    def set_platform_filter(self, platform):
        self._platform = platform

    def set_phase_filter(self, phase):
        self._phase = phase

    def set_os_filter(self, os):
        self._os = os

    def set_name_filter(self, name):
        if isinstance(name, str) or isinstance(name, unicode):
            self._name = {name}
        elif isinstance(name, list):
            self._name = set(name)
        elif isinstance(name, set):
            self._name = name
        else:
            self._name = None
