#!/usr/bin/env python
# =============================================================================
#
# Copyright (c) 2016, Cisco Systems
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
from __future__ import absolute_import
try:
    import click
except ImportError:
    print("Install click python package\n pip install click")
    exit()

import logging
import os
import textwrap
import urlparse
import json
import pprint
import time
import shutil
from csmpe.context import InstallContext
from csmpe.csm_pm import CSMPluginManager
from csmpe.csm_pm import install_phases

_PLATFORMS = ["ASR9K", "NCS4K", "NCS6K", "CRS", "ASR900"]
_OS = ["IOS", "XR", "eXR", "XE"]


def print_plugin_info(pm, detail=False, brief=False):
    for plugin, details in pm.plugins.items():
        platforms = ", ".join(details['platforms'])
        phases = ", ".join(details['phases']) if bool(details['phases']) else "Any"
        os = ", ".join(details['os']) if bool(details['os']) else "Any"
        if brief:
            click.echo("[{}] [{}] [{}] {}".format(platforms, phases, os, details['name']))
        else:
            click.echo("Name: {}".format(details['name']))
            click.echo("Platforms: {}".format(platforms))
            click.echo("Phases: {}".format(phases))
            click.echo("OS: {}".format(os))
            description = "Description: {}\n".format(details['description'])
            description = "\n".join(textwrap.wrap(description, 60))
            click.echo(description)

            if detail:
                click.echo("  UUID: {}".format(plugin))
                package_name = details['package_name']
                click.echo("  Package Name: {}".format(package_name))
                pkginfo = pm.get_package_metadata(package_name)
                click.echo("  Summary: {}".format(pkginfo.summary))
                click.echo("  Version: {}".format(pkginfo.version))
                click.echo("  Author: {}".format(pkginfo.author))
                click.echo("  Author Email: {}".format(pkginfo.author_email))
            click.echo()


def validate_phase(ctx, param, value):
    if value:
        if value.strip() not in install_phases:
            raise click.BadParameter("The supported plugin phases are: {}".format(", ".join(install_phases)))
    return value


class URL(click.ParamType):
    name = 'url'

    def convert(self, value, param, ctx):
        if not isinstance(value, tuple):
            parsed = urlparse.urlparse(value)
            if parsed.scheme not in ('telnet', 'ssh'):
                self.fail('invalid URL scheme (%s).  Only telnet and ssh URLs are '
                          'allowed' % parsed, param, ctx)
        return value


@click.group()
def cli():
    """This script allows maintaining and executing the plugins."""
    pass


@cli.command("list", help="List all the plugins available.", short_help="List plugins")
@click.option("--platform", type=click.Choice(_PLATFORMS),
              help="Supported platform.")
@click.option("--phase", type=click.Choice(install_phases),
              help="Supported phase.")
@click.option("--os", type=click.Choice(_OS),
              help="Supported OS.")
@click.option("--detail", is_flag=True,
              help="Display detailed information about installed plugins.")
@click.option("--brief", is_flag=True,
              help="Display brief information about installed plugins.")
def plugin_list(platform, phase, os, detail, brief):
    pm = CSMPluginManager(None, invoke_on_load=False)
    pm.set_phase_filter(phase)
    pm.set_platform_filter(platform)
    pm.set_os_filter(os)
    pm.load(invoke_on_load=False)

    click.echo("List of installed plugins:\n")
    if platform:
        click.echo("Plugins for platform: {}".format(platform))
    if phase:
        click.echo("Plugins for phase: {}".format(phase))
    if os:
        click.echo("Plugins for os: {}".format(os))

    print_plugin_info(pm, detail, brief)


@cli.command("run", help="Run specific plugin on the device.", short_help="Run plugin")
@click.option("--url", multiple=True, required=True, envvar='CSMPLUGIN_URLS', type=URL(),
              help='The connection url to the host (i.e. telnet://user:pass@hostname). '
                   'The --url option can be repeated to define multiple jumphost urls. '
                   'If no --url option provided the CSMPLUGIN_URLS environment variable is used.')
@click.option("--phase", required=False, type=click.Choice(install_phases),
              help="An install phase to run the plugin for.")
@click.option("--cmd", multiple=True, default=[],
              help='The command to be passed to the plugin in ')
@click.option("--log_dir", default="/tmp", type=click.Path(),
              help="An install phase to run the plugin for. If not path specified then default /tmp directory is used.")
@click.option("--package", default=[], multiple=True,
              help="Package for install operations. This package option can be repeated to provide multiple packages.")
@click.option("--id", default=0, multiple=False,
              help="Package id for install operations.")
@click.option("--repository_url", default=None,
              help="The package repository URL. (i.e. tftp://server/dir")
@click.argument("plugin_name", required=False, default=None)
def plugin_run(url, phase, cmd, log_dir, package, id,  repository_url, plugin_name):

    ctx = InstallContext()
    ctx.hostname = "Hostname"
    ctx.host_urls = list(url)
    ctx.success = False
    ctx.pkg_id = 0

    ctx.requested_action = phase
    ctx.log_directory = log_dir
    session_filename = os.path.join(log_dir, "session.log")
    plugins_filename = os.path.join(log_dir, "plugins.log")
    condoor_filename = os.path.join(log_dir, "condoor.log")

    if os.path.exists(session_filename):
        os.remove(session_filename)
    if os.path.exists(plugins_filename):
        os.remove(plugins_filename)
    if os.path.exists(condoor_filename):
        os.remove(condoor_filename)

    ctx.log_level = logging.DEBUG
    ctx.software_packages = list(package)
    ctx.server_repository_url = repository_url
    ctx.pkg_id = id

    if cmd:
        ctx.custom_commands = list(cmd)

    pm = CSMPluginManager(ctx)
    pm.set_name_filter(plugin_name)
    results = pm.dispatch("run")

    click.echo("\n Plugin execution finished.\n")
    click.echo("Log files dir: {}".format(log_dir))
    click.echo(" {} - device session log".format(session_filename))
    click.echo(" {} - plugin execution log".format(plugins_filename))
    click.echo(" {} - device connection debug log".format(condoor_filename))
    click.echo("Results: {}".format(" ".join(map(str, results))))

@cli.command("test", help="Drive test case runs based on user input or automated", 
                     short_help="Run test case")
@click.option("--config_file", "-c", type=click.Path(exists = True, resolve_path = True, readable = True), 
                help='Config file containing all parameters. Parameters specified on command line'
                     ' override the config file')
@click.option("--admin_active_console", "-adac", type=URL(),
              help='The connection url to the active ADMIN host (i.e. telnet://user:pass@hostname). ')
@click.option("--admin_standby_console", "-adsc", multiple=True, type=URL(),
              help='The connection url to the standby ADMIN host (i.e. telnet://user:pass@hostname). '
                   'The --admin_standby_console option can be repeated to define multiple admin standby hosts.')
@click.option("--xr_active_console", "-xrac", type=URL(),
              help='The connection url to the active XR host (i.e. telnet://user:pass@hostname). ')
@click.option("--xr_standby_console", "-xrsc", multiple=True, type=URL(),
              help='The connection url to the standby XR host (i.e. telnet://user:pass@hostname). '
                   'The --xr_standby_console option can be repeated to define multiple XR standby hosts.')
@click.option("--log_dir", "-l", type=click.Path(),
              help="Log directory. If not specified then default is /tmp")
@click.option("--tc_loc", "-t", type=click.Path(), help="Test case file/dir location")
@click.option("--v1_path", "-v1", type=click.Path(), help="Path for v1 packages")
@click.option("--v2_path", "-v2", type=click.Path(), help="Path for v2 packages")
def jsonparser(config_file, admin_active_console, admin_standby_console, 
        xr_active_console, xr_standby_console, tc_loc, log_dir, v1_path, v2_path):
    oper_plugin = {
                  "Add" : "Install Add Plugin",
                  "Remove" : "Install Remove Plugin",
                  "Remove All" : "Install RemoveAll Plugin",
                  "Remove Inactive" : "Install RemoveInactive Plugin",
                  "Activate" : "Install Activate Plugin",
                  "Deactivate" : "Install Deactivate Plugin",
                  "Commit" : "Install Commit Plugin",
                  "Extract" : "Install Extract Plugin",
                  "Core Check" : "Core Error Check Plugin",
                  "Node Check" : "Node Status Check Plugin",
                  "Command" : "Custom Commands Capture Plugin",
                  "Prepare" : "Install Prepare Plugin",
                  "Flow1" : "Install FirexFlow1 Plugin",
                  "Prepare Clean" : "Install Clean Plugin"
                  }
    tc_list = []
    config = {}
    config['log_dir'] = '/tmp'
    config['tc_loc'] = '/tmp'
    if config_file:
        if os.path.isfile(config_file):
           with open(config_file) as fd_config:
               config.update(json.load(fd_config))
        else:
            raise IOError("Error! Config file not found!!")
    if tc_loc:
        config['tc_loc'] = tc_loc
    if admin_active_console:
        config['admin_active_console'] = admin_active_console
    if admin_standby_console:
        config['admin_standby_console'] = admin_standby_console
    if xr_active_console:
        config['xr_active_console'] = xr_active_console
    if xr_standby_console:
        config['xr_standby_console'] = xr_standby_console
    if log_dir:
        config['log_dir'] = log_dir
    mandatory_args = [ 'xr_active_console' ]
    for arg_name in mandatory_args:
        if not config.get(arg_name):
            raise click.UsageError('{} argument missing.\n Mandatory arguments: {}\n'.format(arg_name, mandatory_args))
    if os.path.isfile(config['tc_loc']):
        tc_list.append(config['tc_loc'])
    elif os.path.isdir(config['tc_loc']):
        tc_list = [os.path.join(config['tc_loc'],f) for f in os.listdir(config['tc_loc']) if f.endswith(".json")]

    if not tc_list:
        raise IOError("Error! No testcase found to run in {}".format(config['tc_loc']))

    log_parent_dir = os.path.join(config['log_dir'], time.strftime("csm-%Y%m%d%H%M%S"))
    for tc_file_org in tc_list:
        print("TC file : {}".format(tc_file_org))
        log_subdir = os.path.splitext(os.path.basename(tc_file_org))[0]
        log_dir = os.path.join(log_parent_dir, log_subdir)
        tc_file = os.path.join(log_dir, 'tc.json') 
        os.makedirs(log_dir)
        shutil.copyfile(tc_file_org, tc_file)
        with open(tc_file) as fd:
            try:
                data = json.load(fd)
            except:
                click.echo("ERROR! Json file {} failed to parse".format(tc_file_org))
                continue
        result_data = []
        for idx, tc in enumerate(data, 1):
            result_i = {
                "tc_id" : idx,
                "message": "Not Run",
                "status": "Blocked",
                "TC": tc["TC"]
            }
            result_data.append(result_i)
        result_file = os.path.join(log_dir, 'result.log')
        with open(result_file, 'w') as fd_log:
            fd_log.write(json.dumps(result_data, indent=4))
        for idx, tc in enumerate(data,1):
            with open(tc_file) as fd:
                data = json.load(fd)
                tc = data[idx - 1]
            #url, phase, cmd, log_dir, package, repository_url, plugin_name
            ctx = InstallContext()
            ctx.hostname = "Hostname"
            urls = []
            if config.get('xr_standby_console'):
                urls.extend(list(config['xr_standby_console']))
            print("DEBUG: Urls {}".format(urls))
            urls.append(config['xr_active_console'])
            urls = [[url.encode('utf8')] if isinstance(url, unicode) else [ url ]for url in urls ]
            ctx.host_urls = urls
            #ctx.host_urls = [ [ "telnet://root:lab@10.105.236.18:2012" ], [ "telnet://root:lab@10.105.236.18:2015" ]]
            print("URL: {}".format(ctx.host_urls))
            ctx.success = False
            ctx.tc_name = tc.get("TC")
            if ctx.tc_name :
                print("Executing TC No {} : {}".format(idx, ctx.tc_name))
            ctx.tc_id = idx
            ctx.shell = tc.get("shell")
            ctx.requested_action = []
            if ctx.shell:
                operation = tc.get("operation")
                if operation:
                    plugin_name = oper_plugin.get(operation)
                    if not plugin_name:
                        print("No plugin found for {}".format(plugin_name))
                        continue
                    else:
                        print("Plugin to be launched {}".format(plugin_name))
                elif tc.get("command"):
                    plugin_name = oper_plugin["Command"]
                    cmd  = tc.get("command")
                    print("Plugin cmd {} with shell {} with plugin {}".format(cmd, ctx.shell, plugin_name))
                    if cmd:
                        if "Bash" in ctx.shell:
                            cmd_list = [ "run " + c for c in cmd]
                            print cmd_list
                            #ctx.requested_action = ["Pre-Upgrade"]
                        ctx._custom_commands = cmd_list
                        print ("Custom command {}".format(ctx.custom_commands))
                    else:
                        print "No command specified to execute"
                        continue 
                else:
                    print "No plugin found. "
                    continue
            else:
                print("Please specify shell as part of TC {}".format(ctx.tc_name))
                break
            ctx.log_directory = log_dir
            ctx.log_level = logging.DEBUG
    
            ctx.software_packages = tc.get("packages",[])
            print ctx.software_packages
            ctx.server_repository_url = tc.get("repository_url")
    
            ctx.pattern = tc.get("pattern",[])
            print("pattern {}".format(ctx.pattern))
    
            ctx.nextlevel = tc.get("nextlevel",[])
            print ctx.nextlevel
            
            ctx.op_id = tc.get("resid",0)
            ctx.issu_mode = tc.get("mode", None)
            ctx.pkg_id = tc.get("pkg_id",[])
            print("CTX: {}".format(json.dumps(ctx.__dict__, indent=4)))
            pm = CSMPluginManager(ctx)
            pm.set_name_filter(plugin_name)
            results = pm.dispatch("run")
            
            #Retain session.log as they get deleted after each plugin execution
            session_filename = os.path.join(log_dir, "session.log")
            session_filename_main = os.path.join(log_dir, "session_main.log")
            with open(session_filename) as sf:
                with open(session_filename_main,"a+")as sfm:
                    for line in sf:
                        sfm.write(line)             
            print("\n Plugin execution finished.\n")
            print("Log files dir: {}".format(log_dir))
            print("Results: {}".format(" ".join(map(str, results))))
                

if __name__ == '__main__':
    cli()
    #jsonparser()


