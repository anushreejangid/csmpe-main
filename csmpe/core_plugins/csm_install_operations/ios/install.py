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
import time

plugin_ctx = None


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


def send_newline(fsm_ctx):
    fsm_ctx.ctrl.sendline('\r\n')
    fsm_ctx.ctrl.sendline('\r\n')
    fsm_ctx.ctrl.sendline('\r\n')
    return True


def issu_error_state(fsm_ctx):
    plugin_ctx.warning("Error in ISSU. Please see session.log for details")
    return False


def wait_for_reload(ctx):
    """
     Wait for system to come up with max timeout as 25 Minutes

    """
    ctx.disconnect()
    time.sleep(180)

    ctx.reconnect(max_timeout=1500)  # 25 * 60 = 1500
    timeout = 3600
    poll_time = 30
    time_waited = 0

    ctx.info("Waiting for the device to come up")
    ctx.post_status("Waiting for the device to come up")
    time.sleep(30)

    output = None

    ncnt = 0
    while 1:

        ncnt += 1
        if ncnt > 20:
            break

        # Wait till all nodes are in XR run state
        time_waited += poll_time
        if time_waited >= timeout:
            break

        time.sleep(poll_time)

        output = ctx.send('show version | include ^System image')

        ctx.info("output = {}".format(output))

        m = re.search('(asr.*\.bin)', output)
        if m:
            ctx.info("The device is in the desired state")
            return True

    # Some nodes did not come to run state
    ctx.error("Not all nodes have came up: {}".format(output))
    # this will never be executed
    return False


def install_activate_write_memory(ctx, cmd, hostname):
    """

    PAN-5201-ASR903#write memory
    Building configuration...
    [OK]
    PAN-5201-ASR903#

    PAN-5201-ASR903#write memory
    Warning: Attempting to overwrite an NVRAM configuration previously written
    by a different version of the system image.
    Overwrite the previous NVRAM configuration?[confirm]

    """
    global plugin_ctx
    plugin_ctx = ctx

    # Seeing this message without the reboot prompt indicates a non-reload situation
    Build_config = re.compile("[OK]")

    Overwrite_warning = re.compile("Overwrite the previous NVRAM configuration?[confirm]")

    Host_prompt = re.compile(hostname)

    events = [Host_prompt, Overwrite_warning, Build_config]
    transitions = [
        (Overwrite_warning, [0], 1, send_newline, 1200),
        (Build_config, [0, 1], 2, None, 1200),
        (Host_prompt, [0, 1, 2], -1, None, 1200),
    ]

    if not ctx.run_fsm("write memory", cmd, events, transitions, timeout=1200):
        ctx.error("Failed: {}".format(cmd))


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


def install_activate_reload(ctx):
    """
    Reload the router

    :param ctx
    :return: nothing
    """
    message = "Waiting the {} operation to continue".format('reload')
    ctx.info(message)
    ctx.post_status(message)

    ctx.reload()

    success = wait_for_reload(ctx)

    if not success:
        ctx.error("Reload or boot failure")
        return

    ctx.info("Operation reload finished successfully")
    return
