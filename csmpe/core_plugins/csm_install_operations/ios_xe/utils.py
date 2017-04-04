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
import string

install_error_pattern = re.compile("Error:    (.*)$", re.MULTILINE)


def log_install_errors(ctx, output):
    """
    Print warning for Error:

    :param ctx:
    :param output:
    :return: nothing
    """
    errors = re.findall(install_error_pattern, output)
    for line in errors:
        ctx.warning(line)


def number_of_rsp(ctx):
    """
    Determine the number of RSP's in the chassis

    :param ctx:
    :return: the number of RSP's
    """
    platforms = ['ASR-902', 'ASR-920']
    count = 0
    valid_count = ['1', '2']

    if ctx._connection.platform in platforms:
        count = 1
        return count

    # show platform can take more than 1 minute after router reload. Issue No. 47
    output = ctx.send("show platform | count RSP", timeout=600)
    if output:
        m = re.search('Number.*= (\d+)', output)
        if m:
            count = m.group(1)
            if count not in valid_count:
                ctx.error("Invalid RSP count: {}".format(count))
            else:
                count = int(count)

    return count


def install_folder(ctx):
    """
    Determine the image folder
        'File: bootflash:/Image/packages.conf, on: RP0'
        'File: consolidated:packages.conf, on: RP0'

    :param   ctx
    :return: the image folder
    """

    folder = 'bootflash:/Image'

    output = ctx.send("show version running | include packages.conf")
    if output:
        m = re.search('File: (.*)/?packages.conf', output)
        if m:
            folder = m.group(1)
            folder = re.sub("/$", "", folder)
            if folder == 'consolidated:':
                folder = 'bootflash:/Image'

    return folder


def create_folder(ctx, folder):
    """
    Determine the image folder
        'File: bootflash:/Image/packages.conf, on: RP0'
        'File: consolidated:packages.conf, on: RP0'

    :param   ctx
    :param   folder to be created
    :return: True: Success, False: Failed
    """

    output = ctx.send('dir ' + folder)
    m = re.search('%Error opening', output)
    if m:
        cmd = 'mkdir ' + folder
        ctx.send(cmd, wait_for_string="Create directory filename")
        ctx.send('\r\n')
    else:
        return True

    output = ctx.send('dir ' + folder)
    m = re.search('%Error opening', output)
    if m:
        return False
    else:
        return True


def available_space(ctx, device):
    """
    Determine the available space on device such as bootflash or stby-bootflash:

    :param ctx:
    :param device: bootflash / stby-bootflash:
    :return: the available space
    """

    available = -1
    output = ctx.send('dir ' + device)
    m = re.search('(\d+) bytes free', output)
    if m:
        available = int(m.group(1))

    return available


def installed_package_name(ctx, pkg_conf):
    """
    :param: ctx
    :param: pkg_conf such as bootflash:/Image/packages.conf
    :return: the installed package name
    """
    output = ctx.send('dir ' + pkg_conf)
    if not output:
        ctx.error("dir {} failed".format(pkg_conf))
        return None

    m = re.search('No such file', output)
    if m:
        ctx.info('{} does not exist'.format(pkg_conf))
        return None

    cmd = "more " + pkg_conf + " | include PackageName"
    output = ctx.send(cmd)
    m = re.search('pkginfo: PackageName: (.*)$', output)
    if m:
        img_name = m.group(1)
        ctx.info("installed package name = {} ".format(img_name))
        return img_name
    else:
        ctx.info("PackageName is not found in {}".format(pkg_conf))
        return None


def installed_package_version(ctx):
    """
    :param: ctx
    :return: the installed package name
    """
    # cmd = "more " + pkg_conf + " | include Build:"
    # pkginfo: Build: 03.14.03.S.155-1.S3-std
    # output = ctx.send(cmd)
    # m = re.search('pkginfo: Build: (.*)$', output)

    cmd = 'show version | include Cisco IOS XE Software'
    output = ctx.send(cmd)
    # Cisco IOS XE Software, Version 03.13.03.S - Extended Support Release
    m = re.search('Version (.*) -', output)

    # Cisco IOS XE Software, Version 03.18.01.SP.156-2.SP1-ext
    if not m:
        m = re.search('Version (.*)$', output)

    if m:
        bld_version = m.group(1)
        ctx.info("installed package version = {}".format(bld_version))
        return bld_version
    else:
        ctx.warning("Build version is not found in show version: {}".format(output))
        return None


def installed_package_device(ctx):
    """
    :param: ctx
    :return: device_type with rsp version ie asr900rsp2
    """
    cmd = 'show version running | include File:'
    # File: bootflash:/Image/asr900rsp2-rpbase.03.13.03.S.154-3.S3-ext.pkg, on: RP0
    # File: bootflash:/Image/asr900rsp3-rpbase.V156_2_SP_SR680887239_5.pkg, on: RP0
    img_dev = None
    output = ctx.send(cmd)
    if output:
        lines = string.split(output, '\n')
        lines = [x for x in lines if x]
        for line in lines:
            m = re.search('File: .*(asr\w+)-\w+.\w+', line)
            if m:
                img_dev = m.group(1)
                break

    ctx.info("installed package device = {}".format(img_dev))
    return img_dev


def install_package_family(pkg):
    """
    :param: pkg ie asr900rsp2-universal.03.13.03.S.154-3.S3-ext.bin
    :return: device_type of the installed image ie asr900
    """
    img_dev = None
    m = re.search('(asr\d+)\w*', pkg)
    if m:
        img_dev = m.group(1)

    return img_dev


def install_add_remove(ctx, cmd):
    """
    Execute the copy command

    :param ctx
    :param cmd
    :return: nothing
    """
    message = "Waiting the operation to continue"
    ctx.info(message)
    ctx.post_status(message)

    ctx.send(cmd, wait_for_string="Destination filename")
    output = ctx.send("\r\n\r\n\r\n", timeout=3600)

    result = re.search("\d+ bytes copied in .* secs", output)

    if result:
        ctx.info("Command {} finished successfully".format(cmd))
        return
    else:
        log_install_errors(ctx, output)
        ctx.error("Command {} failed".format(cmd))


def check_pkg_conf(ctx, folder):
    """
    Remove the existing packages

    :param ctx
    :param folder: i.e. bootflash:/Image
    :return: True or False
    """
    pkg_conf = folder + '/packages.conf'
    output = ctx.send('more ' + pkg_conf + ' | include pkg$')

    if not output:
        return False

    lines = string.split(output, '\n')
    lines = [x for x in lines if x]
    for line in lines:
        if ctx._connection.os_version not in line:
            return False

    return True


def remove_exist_image(ctx, package):
    """
    Remove the existing packages

    :param ctx
    :param package
    :return: True or False
    """

    output = ctx.send('dir ' + package)
    m = re.search('No such file', output)

    if m:
        return True
    else:
        cmd = "del /force {}".format(package)
        ctx.send(cmd)
        ctx.info("Removing files : {}".format(package))

    output = ctx.send(cmd)
    m = re.search('No such file', output)
    if m:
        return True
    else:
        return False


def remove_exist_subpkgs(ctx, folder, pkg):
    """
    Remove residual packages from the earlier installations

    :param ctx
    :param folder: i.e. bootflash:/Image
    :return: True or False
    """

    pkg_conf = folder + '/packages.conf'
    # Skip if no packages.conf
    output = ctx.send('dir ' + pkg_conf)
    if not output:
        ctx.error("dir {} failed".format(pkg_conf))
        return

    m = re.search('No such file', output)
    if m:
        ctx.info('Booted from consolidated mode: '
                 '{} does not exist'.format(pkg_conf))
        return

    # Discover package name, version, and image device
    img_name = installed_package_name(ctx, pkg_conf)
    bld_version = installed_package_version(ctx)
    img_device = installed_package_device(ctx)

    if not bld_version or not img_device or not img_name:
        ctx.warning("Not able to determine package name, version, or image device.")
        ctx.warning("Packages left over from earlier installations will not be removed.")
        return

    # Remove all the bin files except the current install pkg

    if folder != 'bootflash:':
        package_name = folder + '/asr*.bin'
        remove_exist_image(ctx, package_name)
    else:
        package_name = folder + '*.bin'
        output = ctx.send('dir ' + package_name + ' | include bin')
        if not output:
            ctx.error("dir {} failed".format(package_name))
            return

        lines = string.split(output, '\n')
        lines = [x for x in lines if x]
        for line in lines:
            m = re.search('(asr.*\.bin)', line)
            if m:
                previous_pkg = m.group(0)
                if previous_pkg != pkg:
                    previous_package = folder + '/' + previous_pkg
                    remove_exist_image(ctx, previous_package)

    # Remove the packages.conf*- file
    package_name = folder + '/packages.conf*-'
    remove_exist_image(ctx, package_name)

    # Remove residual asr900*.conf
    package_name = folder + '/asr9*.conf'
    remove_exist_image(ctx, package_name)

    # Remove .pkg files
    cmd = 'dir ' + folder + '/*.pkg | include pkg'
    # Directory of bootflash:/Image/*.pkg
    # 15107  -rw-    41534024   Sep 8 2016 03:55:47 +00:00  asr900rsp2-espbase.03.14.03.S.155-1.S3-std.pkg
    output = ctx.send(cmd)

    if not output:
        return

    lines = string.split(output, '\n')
    lines = [x for x in lines if x]
    for line in lines:
        m = re.search('(asr9.*pkg)', line)
        if m:
            exfile = m.group(1)
            package = folder + '/' + exfile
            if bld_version not in package or img_device not in package:
                remove_exist_image(ctx, package)

    return


def check_issu_readiness(ctx, pkg, image_size):
    """
    Expand the consolidated file into the image folder

    :param: ctx
    :param: pkg
    :param: image_size
    :return: True or False
    """

    # check the current package mode
    cmd = 'show version | count packages.conf'
    output = ctx.send(cmd)
    if output:
        m = re.search('Number.*= (\d+)', output)
        if m:
            count = m.group(1)
            if count == '0':
                ctx.info("The current boot mode is consolidated package.")
                return False
        else:
            ctx.warning("Invalid show version output: {}".format(output))
            return False
    else:
        ctx.warning("Show version command error!")
        return False

    # check software compatibility
    cmd = 'show version | include System image file'
    output = ctx.send(cmd)
    if output:
        m = re.search('System image file is \"(.*)\"', output)
        if m:
            pkg_conf = m.group(1)
            img_name = installed_package_name(ctx, pkg_conf)
            if not img_name:
                ctx.warning("Installed package name {} is not found.".format(pkg_conf))
                return False
        else:
            ctx.warning("Show version command error!")
            return False
    else:
        ctx.warning("Show version command error!")
        return False

    m = re.search('asr\w+-(\w+)\.\w+', pkg)
    if m:
        pkg_name = m.group(1)
        if img_name != pkg_name:
            ctx.info("Incompatible packages: {} vs. {}".format(img_name, pkg_name))
            return False
    else:
        ctx.warning("Package name is not found in {}".format(pkg))
        return False

    # check image types between RSP's
    cmd = 'show version rp active running | include Package'
    output = ctx.send(cmd)
    cmd = 'show version rp standby running | include Package'
    stby_output = ctx.send(cmd)
    if output and stby_output:
        lines = string.split(output, '\n')
        lines = [x for x in lines if x]
        # Package: rpbase, version: 03.16.00.S.155-3.S-ext, status: active
        for line in lines:
            m = re.search('Package: (.*) status', line)
            if m:
                img_type = m.group(1)
                if img_type not in stby_output:
                    ctx.warning("Mismatched image types:")
                    ctx.warning("Active rp version: {}".format(output))
                    ctx.warning("Standby rp version: {}".format(stby_output))
                    return False
            else:
                ctx.warning("Invalid package version format: {}".format(line))
                return False
    else:
        ctx.warning("Show version command error!")
        return False

    # check the required disk space for ISSU
    # bootflash: requires additional 250 MB
    # stby-bootflash: requires additional 450 MB
    total_size = 250000000 + image_size
    flash_free = available_space(ctx, 'bootflash:')
    if flash_free < total_size:
        ctx.info("Total required / bootflash "
                 "available: {} / {} bytes".format(total_size, flash_free))
        ctx.info("Not enough space in bootflash: to perform ISSU. "
                 "Setting the Router to boot in sub-package mode.")
        return False

    total_size = 450000000 + image_size
    flash_free = available_space(ctx, 'stby-bootflash:')
    if flash_free < total_size:
        ctx.info("Total required / stby-bootflash "
                 "available: {} / {} bytes".format(total_size, flash_free))
        ctx.info("Not enough space in stby-bootflash: to perform ISSU. "
                 "Setting the Router to boot in sub-package mode.")
        return False
    else:
        ctx.info("There is enough space on bootflash and stby-bootflash to perform ISSU")

    # check show redundancy
    cmd = 'show redundancy | include Configured Redundancy Mode'
    output = ctx.send(cmd)
    if output:
        m = re.search('Configured Redundancy Mode = (.*)', output)
        if m:
            configed_mode = m.group(1)
            if configed_mode != 'sso':
                ctx.warning("Configured Redundancy Mode = {}".format(configed_mode))
                return False
        else:
            ctx.warning("Show redundancy command error!")
            return False
    else:
        ctx.warning("Show redundancy command error!")
        return False

    cmd = 'show redundancy | include Operating Redundancy Mode'
    output = ctx.send(cmd)
    if output:
        m = re.search('Operating Redundancy Mode = (.*)', output)
        if m:
            operating_mode = m.group(1)
            if operating_mode != 'sso':
                ctx.warning("Operating Redundancy Mode = {}".format(operating_mode))
                return False
        else:
            ctx.warning("Show redundancy command error!")
            return False
    else:
        ctx.warning("Show redundancy command error!")
        return False

    cmd = 'show redundancy | include Current Software state'
    output = ctx.send(cmd)
    if output:
        lines = string.split(output, '\n')
        lines = [x for x in lines if x]
        num_of_line = len(lines)
        if num_of_line != 2:
            ctx.warning("num_of_line = {}".format(num_of_line))
            ctx.warning("Current Software state = {}".format(output))
            return False

        m = re.search('Current Software state = (.*)', lines[0])
        if m:
            active_state = m.group(1)
            if 'ACTIVE' not in active_state:
                ctx.warning("show redundancy Active state check has failed")
                ctx.warning("active_state = {}".format(active_state))
                ctx.warning("Current Software state = {}".format(lines[0]))
                return False
        else:
            ctx.warning("Show redundancy command error!")
            return False

        m = re.search('Current Software state = (.*)', lines[1])
        if m:
            stby_state = m.group(1)
            if 'STANDBY HOT' not in stby_state:
                ctx.warning("show redundancy STANDBY HOT state check has failed")
                ctx.warning("stby_state = {}".format(stby_state))
                ctx.warning("Current Software state = {}".format(lines[1]))
                return False
        else:
            ctx.warning("Show redundancy command error!")
            return False

    else:
        ctx.warning("Show redundancy command error!")
        return False

    return True


def xe_show_platform(ctx):
    """
    Parse show platform output to extract the RP and SIP status
    :param: ctx
    :return: dictionary

    0         1         2         3         4         5         6
    012345678901234567890123456789012345678901234567890123456789012345678
    Slot      Type                State                 Insert time (ago)
    --------- ------------------- --------------------- -----------------
     0/0      12xGE-2x10GE-FIXED  ok                    15:09:04
    R1        A900-RSP2A-128      ok, active            14:09:30
    """
    platform_info = {}
    cmd = 'show platform'
    # show platform can take more than 1 minute after router reload. Issue No. 47
    output = ctx.send(cmd, timeout=600)
    if output:
        lines = string.split(output, '\n')
        lines = [x for x in lines if x]
        sip0 = False
        for line in lines:
            if not sip0:
                m = re.search('--------- ------------------- '
                              '--------------------- -----------------', line)
                if m:
                    sip0 = True
                continue

            m = re.search('Slot      CPLD Version        Firmware Version', line)
            if m:
                break

            Slot = line[:8].strip()
            Type = line[10:28].strip()
            State = line[30:50].strip()

            m1 = re.search('^0\/\d+', Slot)
            m2 = re.search('^R\d+', Slot)
            if m1 or m2:
                platform_info[Slot] = [Type, State]

    return platform_info
