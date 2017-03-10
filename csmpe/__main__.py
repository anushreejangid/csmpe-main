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

try:
    import click
except ImportError:
    print("Install click python package\n pip install click")
    exit()

import logging
import os
import textwrap
import urlparse

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
@click.option("--repository_url", default=None,
              help="The package repository URL. (i.e. tftp://server/dir")
@click.argument("plugin_name", required=False, default=None)
def plugin_run(url, phase, cmd, log_dir, package, repository_url, plugin_name):

    ctx = InstallContext()
    ctx.hostname = "Hostname"
    ctx.host_urls = list(url)
    ctx.success = False

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


if __name__ == '__main__':
    cli()
