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
from csmpe.plugins import CSMPlugin
from utils import available_space
from utils import number_of_rsp
from utils import install_folder
from utils import check_issu_readiness
from utils import remove_exist_subpkgs
from utils import install_package_family
from utils import create_folder
from utils import xe_show_platform
from utils import check_pkg_conf


class Plugin(CSMPlugin):
    """This plugin performs pre-activate tasks."""
    name = "Install Pre-Activate Plugin"
    platforms = {'ASR900'}
    phases = {'Pre-Activate'}
    os = {'XE'}

    def run(self):

        self.ctx.info("Hardware platform: {}".format(self.ctx._connection.platform))
        self.ctx.info("OS Version: {}".format(self.ctx._connection.os_version))

        try:
            packages = self.ctx.software_packages
        except AttributeError:
            self.ctx.warning("No package list provided. Skipping calculation of required free bootflash memory.")
            return

        pkg = ''.join(packages)
        con_platforms = ['ASR-902', 'ASR-920']
        sub_platforms = ['ASR-903', 'ASR-907']
        rsp_count = 1
        folder = 'bootflash:'
        stby_folder = 'stby-bootflash:'

        # check the device type vs the package family
        supported_imgs = {}
        supported_imgs['asr902'] = ['asr900', 'asr903']
        supported_imgs['asr903'] = ['asr900', 'asr903']
        supported_imgs['asr907'] = ['asr900', 'asr903']
        supported_imgs['asr920'] = ['asr920']

        m = re.search('ASR-(\d+)', self.ctx._connection.platform)
        if m:
            device_family = m.group(1)
            device_family = 'asr' + device_family
        else:
            self.ctx.error("Unspported device: {}".format(self.ctx._connection.platform))
            return

        pkg_family = install_package_family(pkg)

        if not pkg_family:
            self.ctx.info("Private device image: {}".format(pkg))

        if pkg_family not in supported_imgs[device_family]:
            self.ctx.info("Private device image: {} on {}".format(pkg, self.ctx._connection.platform))

        # check the RSP type between image and device:
        curr_rsp = None
        pkg_rsp = None

        output = self.ctx.send("show version | include RSP")
        if output:
            m = re.search('(RSP\d)', output)
            if m:
                curr_rsp = m.group(0).lower()

            m = re.search('(rsp\d)', pkg)
            if m:
                pkg_rsp = m.group(0)

            if curr_rsp and pkg_rsp and curr_rsp != pkg_rsp:
                self.ctx.info("Incompatible Route processor in {} for this device {}".format(pkg, curr_rsp))

        # Determine one of the following modes: consolidated, subpackage, or issu

        if self.ctx._connection.platform in con_platforms:
            mode = 'consolidated'
        elif self.ctx._connection.platform in sub_platforms:
            mode = 'subpackage'
            # Determine the number of RSP's in the chassis
            rsp_count = number_of_rsp(self.ctx)
            if rsp_count == 0:
                self.ctx.error("No RSP is discovered")
                return

            # Determine the install folder
            folder = install_folder(self.ctx)
            stby_folder = 'stby-' + folder

            # Create the folder if it does not exist
            if not create_folder(self.ctx, folder):
                self.ctx.error("Install folder {} creation failed", format(folder))
                return

            if rsp_count == 2 and not create_folder(self.ctx, stby_folder):
                self.ctx.error("Install folder {} creation "
                               "failed", format(stby_folder))
                return
        else:
            self.ctx.error("Unsupported platform: {}".format(self.ctx._connection.platform))
            return

        total_size = 10000000

        valid_pkg_conf = False
        if mode == 'subpackage':
            # Check if the packages.conf is valid
            valid_pkg_conf = check_pkg_conf(self.ctx, folder)

            # Remove residual image files from previous installations
            if valid_pkg_conf:
                remove_exist_subpkgs(self.ctx, folder, pkg)
            else:
                self.ctx.warning("Empty or invalid {}/packages.conf".format(folder))
                self.ctx.warning("Residual packages from previous installations are not "
                                 "automatically removed from bootflash: / stby-bootflash:.")
                self.ctx.info("Sub-package mode will be performed to "
                              "activate package = {}".format(pkg))

            cmd = "dir bootflash: | include " + pkg
            output = self.ctx.send(cmd)
            if output:
                m = re.search('-rw-\s+(\d+)\s+', output)
                if m:
                    total_size += int(m.group(1))

        flash_free = available_space(self.ctx, 'bootflash:')
        self.ctx.info("Total required / bootflash "
                      "available: {} / {} bytes".format(total_size, flash_free))
        if flash_free < total_size:
            self.ctx.error("Not enough space on bootflash: to install packages. "
                           "The install process can't proceed.\n"
                           "Please erase unused images, crashinfo, "
                           "core files, and tracelogs")
        else:
            self.ctx.info("There is enough space on bootflash: to install packages.")

        if rsp_count == 2:
            if valid_pkg_conf:
                remove_exist_subpkgs(self.ctx, stby_folder, pkg)
            stby_free = available_space(self.ctx, 'stby-bootflash:')
            self.ctx.info("Total required / stby-bootflash "
                          "available: {} / {} bytes".format(total_size, stby_free))
            if stby_free < total_size:
                self.ctx.error("Not enough space on stby-bootflash: to "
                               "install packages. The install process can't proceed.\n"
                               "Please erase unused images, crashinfo, core files, "
                               "and tracelogs")
            else:
                self.ctx.info("There is enough space on stby-bootflash: to install packages.")

        # Determine if ISSU is feasible
        if mode == 'subpackage' and rsp_count == 2 and valid_pkg_conf:
            if check_issu_readiness(self.ctx, pkg, total_size):
                mode = 'issu'
                self.ctx.info("ISSU will be performed to activate package = {}".format(pkg))

        # Log the status of RP and SIP
        platform_info = xe_show_platform(self.ctx)
        if not platform_info:
            self.ctx.error("The CLI 'show platform' is not able to determine the status of RP and SIP ")
            return
        self.ctx.info("show platform = {}".format(platform_info))

        self.ctx.info("Activate number of RSP = {}".format(rsp_count))
        self.ctx.info("Activate package = {}".format(pkg))
        self.ctx.info("Install folder = {}".format(folder))
        self.ctx.info("Activate package mode = {}".format(mode))

        self.ctx.save_data('xe_rsp_count', rsp_count)
        self.ctx.save_data('xe_activate_pkg', pkg)
        self.ctx.save_data('xe_boot_mode', mode)
        self.ctx.save_data('xe_install_folder', folder)
        self.ctx.save_data('xe_show_platform', platform_info)

        return True
