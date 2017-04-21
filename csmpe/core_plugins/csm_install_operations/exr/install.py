# coding=utf-8
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
from functools import partial
import os
import itertools
import re
import time
import json
from condoor import ConnectionError, CommandError, ConnectionTimeoutError
from csmpe.core_plugins.csm_node_status_check.exr.plugin_lib import parse_show_platform
from csmpe.core_plugins.csm_install_operations.actions import a_error

install_error_pattern = re.compile("Error:    (.*)$", re.MULTILINE)

plugin_ctx = None


def log_install_errors(ctx, output):
        errors = re.findall(install_error_pattern, output)
        for line in errors:
            ctx.warning(line)


def check_ncs6k_release(ctx):
    """
    Only release 5.2.5 and above are supported by the plugin.
    """
    if ctx.family == 'NCS6K':
        packages = ctx.software_packages
        if packages is not None:
            for package_name in packages:
                matches = re.findall("\d+\.\d+\.\d+", package_name)
                if matches:
                    if matches[0] < '5.2.5':
                        ctx.error('Abort: Software package earlier than release 5.2.5 for NCS6K is not supported.')


def check_ncs4k_release(ctx):
    """
    Only release 6.0.2 and above are supported by the plugin.
    """
    if ctx.family == 'NCS4K':
        packages = ctx.software_packages
        if packages is not None:
            for package_name in packages:
                matches = re.findall("\d+\.\d+\.\d+", package_name)
                if matches:
                    if matches[0] < '6.0.2':
                        ctx.error('Abort: Software package earlier than release 6.0.2 for NCS4K is not supported.')


def watch_operation(ctx, op_id=0):
    """
    Watch for the non-reload situation.  Upon issuing add/activate/commit/remove/deactivate, the install operation
    will be executed in the background.  The following message

    Install operation will continue in the background

    will be displayed.  After some time elapses, a successful or abort message will be displayed.

    The CLI command, 'show install request' is used in the loop to report the progress percentages.  Upon
    completion, 'show install request' returns 'No install operation in progress'.  The watch_operation will be
    done at that point.

    As an example,

    RP/0/RP0/CPU0:Deploy#install deactivate ncs6k-5.2.5.CSCuz65240-1.0.0
    May 31 20:14:14 Install operation 3 started by root:
      install deactivate pkg ncs6k-5.2.5.CSCuz65240-1.0.0
    May 31 20:14:14 Package list:
    May 31 20:14:14     ncs6k-5.2.5.CSCuz65240-1.0.0
    May 31 20:14:20 Install operation will continue in the background

    <--- Time Lapse --->

    RP/0/RP0/CPU0:Deploy#May 31 20:15:10 Install operation 3 finished successfully

    ------------------------------------------------------------------------------------------------------------
    RP/0/RP0/CPU0:Deploy#show install request
    The install operation 17 is 30% complete

    or

    RP/0/RP0/CPU0:Deploy#show install request
    No install operation in progress

    When install is completed, the following message will be displayed

    ------------------------------------------------------------------------------------------------------------
    If the install operation is successful, the following message will be displayed.

    RP/0/RP0/CPU0:Deploy#May 24 22:25:43 Install operation 17 finished successfully
    """
    no_install = r"No install operation in progress"
    # In ASR9K eXR, the output to show install request may be "The install prepare operation 9 is 40% complete"
    # or "The install service operation 9 is 40% complete" or "The install add operation 9 is 40% complete" and etc.
    op_progress = r"The install \w*?\s?operation {} is (\d+)% complete".format(op_id)
    success = "Install operation {} completed|finished successfully".format(op_id)

    cmd_show_install_request = "show install request"
    ctx.info("Watching the operation {} to complete".format(op_id))

    propeller = itertools.cycle(["|", "/", "-", "\\", "|", "/", "-", "\\"])

    last_status = None
    finish = False
    time_tried = 0
    while not finish:
        try:
            try:
                # this is to catch the successful operation as soon as possible
                ctx.send("", wait_for_string=success, timeout=20)
                finish = True
            except ctx.CommandTimeoutError:
                pass
            message = ""
            output = ctx.send(cmd_show_install_request, timeout=300)
            if op_id in output:
                result = re.search(op_progress, output)
                if result:
                    status = result.group(0)
                    message = "{} {}".format(propeller.next(), status)

                if message != last_status:
                    ctx.post_status(message)
                    last_status = message
        except (ConnectionError, ctx.CommandTimeoutError) as e:
            if time_tried > 2:
                raise e

            time_tried += 1
            ctx.disconnect()
            time.sleep(60)
            ctx.reconnect(force_discovery=True)

        if no_install in output:
            break

    #report_install_status(ctx, op_id)


def validate_node_state(inventory):
    valid_state = [
        'IOS XR RUN',
        'PRESENT',
        'READY',
        #'FAILED',
        'OK',
        'DISABLED',
        'UNPOWERED',
        'POWERED_OFF',
        #'SW_INACTIVE',
        #'ADMIN DOWN',
        'OPERATIONAL',
        'NOT ALLOW ONLIN',  # This is not spelling error
    ]

    for key, value in inventory.items():
        if 'CPU' in key:
            if value['state'] not in valid_state:
                break
    else:
        return True

    return False


def wait_for_reload(ctx):
    """
     Wait for system to come up with max timeout as 25 Minutes

    """
    begin = time.time()
    pattern_to_match = r"RP\/0\/RP0\/CPU0\:ios(\([^()]*\))?#|RP\/[0-3]\/RS?P[0-1](?:\/CPU[0-3])?:ios#|rommon \d+ >|XML>"
    if not ctx.is_console:
        ctx.disconnect()
        ctx.post_status("Waiting for device boot to reconnect")
        ctx.info("Waiting for device boot to reconnect")
        time.sleep(60)
        ctx.reconnect(max_timeout=1500, force_discovery=True)  # 25 * 60 = 1500

    else:
        ctx.info("Keeping console connected")
        ctx.post_status("Boot process started")
        ctx.info("Boot process started")
        #time.sleep(200)
        #ctx.disconnect()
        try:
            ctx.reload(reload_timeout=1500, no_reload_cmd=True)  # 25 * 60 = 1500
        except (ConnectionTimeoutError, ConnectionError) as e:
            ctx.post_status("Connection error: {}".format(e))
            try:
                ctx.post_status("{}".format(ctx._connection.is_connected()))
            except:
                pass
            try:
                ctx.post_status("Trying to disconnect")
                ctx.disconnect()
                ctx.post_status("Disconnected")
            except:
                pass
            try:
                ctx.post_status("{}".format(ctx._connection.is_connected()))
            except:
                pass
            try: 
                ctx.post_status("Trying to reconnect")
                ctx.connect(force_discovery=True)
                ctx.post_status("Reconnected")
            except:
                pass
    try:
        ctx.post_status("{}".format(ctx._connection.is_connected()))
    except:
        pass
    ctx.info("Boot process finished")
    ctx.info("Device connected successfully")

    timeout = 3600
    poll_time = 30
    time_waited = 0
    xr_run = "IOS XR RUN"

    cmd = "show platform"
    ctx.info("Waiting for all nodes to come up")
    ctx.post_status("Waiting for all nodes to come up")

    time.sleep(100)

    while 1:
        # Wait till all nodes are in XR run state
        time_waited += poll_time
        if time_waited >= timeout:
            break

        time.sleep(poll_time)

        # show platform can take more than 1 minute after router reload. Issue No. 47
        try:
            if ctx.shell == "Admin":
                ctx.info("Switching to admin mode")
                ctx.send("admin", timeout=30)   
        except:
            pass    
        output = ctx.send(cmd, wait_for_string=pattern_to_match , timeout=600)
        if xr_run in output:
            inventory = parse_show_platform(output)
            if validate_node_state(inventory):
                ctx.info("All nodes in desired state")
                elapsed = time.time() - begin
                ctx.info("Overall outage time: {} minute(s) {:.0f} second(s)".format(elapsed // 60, elapsed % 60))
                return True

    # Some nodes did not come to run state
    report_log(ctx, False, "Not all nodes have came up: {}".format(output))
    ctx.error("Not all nodes have came up: {}".format(output))
    # this will never be executed
    return False

def observe_install_add_remove(ctx, output, has_tar=False):
    """
    Success Condition:
    ADD:
    install add source tftp://223.255.254.254/auto/tftpboot-users/alextang/ ncs6k-mpls.pkg-6.1.0.07I.DT_IMAGE
    May 24 18:54:12 Install operation will continue in the background
    RP/0/RP0/CPU0:Deploy#May 24 18:54:30 Install operation 12 finished successfully

    REMOVE:
    RP/0/RP0/CPU0:Deploy#install remove ncs6k-5.2.5.47I.CSCux97367-0.0.15.i
    May 23 21:20:28 Install operation 2 started by root:
      install remove ncs6k-5.2.5.47I.CSCux97367-0.0.15.i
    May 23 21:20:28 Package list:
    May 23 21:20:28     ncs6k-5.2.5.47I.CSCux97367-0.0.15.i
    May 23 21:20:29 Install operation will continue in the background

    RP/0/RP0/CPU0:Deploy#May 23 21:20:29 Install operation 2 finished successfully

    Failed Condition:
    RP/0/RSP0/CPU0:CORFU#install remove ncs6k-5.2.5.47I.CSCux97367-0.0.15.i
    Mon May 23 22:57:45.078 UTC
    May 23 22:57:46 Install operation 28 started by iox:
      install remove ncs6k-5.2.5.47I.CSCux97367-0.0.15.i
    May 23 22:57:46 Package list:
    May 23 22:57:46     ncs6k-5.2.5.47I.CSCux97367-0.0.15.i
    May 23 22:57:47 Install operation will continue in the background

    RP/0/RSP0/CPU0:CORFU#May 23 22:57:48 Install operation 28 aborted
    """
    result = re.search('nstall operation (\d+)', output)
    if result:
        op_id = result.group(1)
        ctx.operation_id = op_id
        if has_tar is True:
            ctx.info("The operation {} stored".format(op_id))
    else:
        report_install_status(ctx, output=output)
        return  # for sake of clarity

    op_success = "Install operation will continue in the background"
    if ctx.nextlevel:
        nextlevel_processing(ctx)
    if op_success in output:
        watch_operation(ctx, op_id)
    else:
        log_install_errors(ctx, output)
    report_install_status(ctx, ctx.operation_id)
        #ctx.error("Operation {} failed".format(op_id))

def get_sysadmin_op_id(output):
    global plugin_ctx
    result = re.search('Op Id (\d+)', output)
    if result:
        return result.group(1)

def get_op_id(output):
    """
    :param output: Output from the install command
    :return: the operational ID
    """
    result = re.search('Install operation (\d+)', output)
    if result:
        return result.group(1)
    else:
        op_progress = r"User admin, Op Id (\d+)"
        cmd_show_install_request = "show install request"
        output = plugin_ctx.send(cmd_show_install_request, timeout=300)
        result = re.search(op_progress, output)
        if result:
            plugin_ctx.op_id = result.group(1)
            return plugin_ctx.op_id
    return -1

def report_log(ctx, status, message="No output to match pattern"):
    result_file = os.path.join(ctx.log_directory, 'result.log')
    with open(result_file, 'r') as fd_log:
      data = json.load(fd_log)
    tc_id = ctx.tc_id - 1
    data[tc_id]['status'] = 'Pass' if status else 'Fail'
    data[tc_id]['message'] = message
    with open(result_file, 'w') as fd_log:
        fd_log.write(json.dumps(data, indent=4))
    ctx.post_status("tc_id: {}, TC: {} :: {}".format(ctx.tc_id, ctx.tc_name, message))

def report_install_status(ctx, op_id=None, output=None):
    """
    :param ctx: CSM Context object
    :param op_id: operational ID
    Peeks into the install log to see if the install operation is successful or not
    """
    try:
        if ctx.shell == "Admin":
            ctx.info("Switching to admin mode")
            ctx.send("admin", timeout=30)
    except:
        pass
    if op_id:
        failed_oper = r'failed|aborted|error'
        output = ctx.send("show install log {} detail".format(op_id))
        ctx.info("DEBUG: Output {}".format(output))
        status, message = match_pattern(ctx.pattern, output)
        report_log(ctx, status, message)
        log_install_errors(ctx, output)
        if not status:
            ctx.error("Operation {} failed".format(op_id))
        else:
            if re.search(failed_oper, output):
                ctx.post_status("Operation {} failed".format(op_id))
            else:
                ctx.post_status("Operation {} finished successfully".format(op_id))
    else:
        status, message = match_pattern(ctx.pattern, output)
        report_log(ctx, status, message)
        log_install_errors(ctx, output)
        if not status:
            ctx.error("Operation failed with no op-id")
        else:
            ctx.post_status("Operation failed with no op-id")
    return status
  

def handle_aborted(fsm_ctx):
    """
    :param ctx: FSM Context
    :return: True if successful other False
    """
    global plugin_ctx
    if plugin_ctx.nextlevel:
        nextlevel_processing(plugin_ctx)
    report_install_status(ctx=plugin_ctx, op_id=get_op_id(fsm_ctx.ctrl.before))

    # Indicates the failure
    return False


def handle_non_reload_activate_deactivate(fsm_ctx):
    """
    :param ctx: FSM Context
    :return: True if successful other False
    """
    global plugin_ctx
    plugin_ctx.info("handle_non_reload_activate_deactivate")
    plugin_ctx.info("Before {}".format(fsm_ctx.ctrl.before))
    plugin_ctx.info("{}".format(fsm_ctx.ctrl.after))
    out = fsm_ctx.ctrl.before
    op_id = get_op_id(fsm_ctx.ctrl.before)
    if plugin_ctx.nextlevel:
        nextlevel_processing(plugin_ctx)
    if op_id == -1:
        status = report_install_status(plugin_ctx, output=out)
        return True
    watch_operation(plugin_ctx, op_id)
    report_install_status(plugin_ctx, op_id)
    return True


def handle_reload_activate_deactivate(fsm_ctx):
    """
    :param ctx: FSM Context
    :return: True if successful other False
    """
    global plugin_ctx
    plugin_ctx.info("handle_reload_activate_deactivate")
    op_id = get_op_id(fsm_ctx.ctrl.before)
    if op_id == -1:
        return False

    if plugin_ctx.nextlevel:
        nextlevel_processing(plugin_ctx)
    try:
        watch_operation(plugin_ctx, op_id)
    except plugin_ctx.CommandTimeoutError:
        # The device already started the reload
        pass

    success = wait_for_reload(plugin_ctx)
    if not success:
        plugin_ctx.error("Reload or boot failure")
        return
    report_install_status(plugin_ctx, op_id)
    plugin_ctx.info("Operation {} finished successfully".format(op_id))

    return True

def handle_issu_reload(fsm_ctx):
    """This handles a reload requiring a yes to start the op"""
    global plugin_ctx
    plugin_ctx.info("handle_issu_reload")
    plugin_ctx.send("yes", timeout=30)
    nextlevel = plugin_ctx.nextlevel
    if nextlevel:
        nextlevel_processing(plugin_ctx)
    cmd_show_install_request = "show install request"
    op_id = 0
    while op_id <= 0:
        output = plugin_ctx.send(cmd_show_install_request, timeout=30)
        op_id = get_op_id(output)
    try:
        watch_operation(plugin_ctx, op_id)
    except plugin_ctx.CommandTimeoutError:
        plugin_ctx.info("The device already started the reload")
        pass
    #status = report_install_status(plugin_ctx, op_id)
    success = wait_for_reload(plugin_ctx)
    if not success:
        report_log(ctx, False, "Reload or boot failure")
        plugin_ctx.error("Reload or boot failure")
        return False
    report_install_status(plugin_ctx, op_id)
    return success

def handle_admin_reload(fsm_ctx):
    global plugin_ctx
    pattern_to_match = r"RP\/0\/RP0\/CPU0\:ios(\([^()]*\))?#|RP\/[0-3]\/RS?P[0-1](?:\/CPU[0-3])?:ios#|rommon \d+ >|XML>|\w*sysadmin-vm:\w*"
    xr_run = "IOS XR RUN"
    plugin_ctx.send("yes", timeout=30)
    cmd_show_install_request = "show install request"
    op_id = 0
    while op_id <= 0:
        output = plugin_ctx.send(cmd_show_install_request, timeout=30)
        time.sleep(30)
        op_id = get_sysadmin_op_id(output)
    try:
        if ctx.shell == "Admin":
            ctx.info("Switching to admin mode")
            ctx.send("admin", timeout=30)   
    except:
        pass           
    try:
        watch_operation(plugin_ctx, op_id)
    except plugin_ctx.CommandTimeoutError:
        plugin_ctx.info("The device already started the reload")
        pass
    time.sleep(150)
    status = report_install_status(plugin_ctx, op_id)
    #success = wait_for_reload(plugin_ctx)
    #if not success:
        #report_log(ctx, False, "Reload or boot failure")
        #plugin_ctx.error("Reload or boot failure")
        #return False
    try:
        if plugin_ctx.shell == "Admin":
            output = plugin_ctx.send("admin", timeout=30)
    except:
        pass
    status = report_install_status(plugin_ctx, op_id)
    cmd = "show platform"
    output = plugin_ctx.send(cmd, wait_for_string=pattern_to_match , timeout=600)
    if xr_run in output:
        inventory = parse_show_platform(output)
        if validate_node_state(inventory):
            plugin_ctx.info("All nodes in desired state")
            elapsed = time.time() - begin
            plugin_ctx.info("Overall outage time: {} minute(s) {:.0f} second(s)".format(elapsed // 60, elapsed % 60))
            return True and status
    
    return status and False

def no_impact_warning(fsm_ctx):
    global plugin_ctx
    plugin_ctx.warning("This was a NO IMPACT OPERATION. Packages are already active/inactive on device.")
    plugin_ctx.info("after {}".format(fsm_ctx.ctrl.after))
    plugin_ctx.info("before {}".format(fsm_ctx.ctrl.before))
    op_id = get_op_id(fsm_ctx.ctrl.before)
    plugin_ctx.info("Op id: {}".format(op_id))
    if plugin_ctx.nextlevel:
        nextlevel_processing(plugin_ctx)
    report_install_status(plugin_ctx, op_id, fsm_ctx.ctrl.after)
    return True


def handle_not_start(fsm_ctx):
    """
    :param ctx: FSM Context
    :return: False
    """
    global plugin_ctx

    plugin_ctx.error("Could not start this install operation because an install operation is still in progress")
    if plugin_ctx.nextlevel:
        nextlevel_processing(plugin_ctx)
    return False

def handle_op_after_su(fsm_ctx):
    """
    :param ctx: FSM Context
    :return: False
    """
    global plugin_ctx
    plugin_ctx.info("after {}".format(fsm_ctx.ctrl.after))
    plugin_ctx.info("before {}".format(fsm_ctx.ctrl.before))
    if plugin_ctx.nextlevel:
        nextlevel_processing(plugin_ctx)
    report_install_status(plugin_ctx, output=fsm_ctx.ctrl.after)
    return True

def handle_admin_op_failure(fsm_ctx):
    global plugin_ctx
    plugin_ctx.info("after {}".format(fsm_ctx.ctrl.after))
    plugin_ctx.info("before {}".format(fsm_ctx.ctrl.before))
    if plugin_ctx.nextlevel:
        nextlevel_processing(plugin_ctx)
    report_install_status(plugin_ctx, output=fsm_ctx.ctrl.after)
    return True

def install_activate_deactivate(ctx, cmd):
    """
    Abort Situation:
    RP/0/RP0/CPU0:Deploy#install activate ncs6k-5.2.5.CSCuz65240-1.0.0

    Jun 02 20:19:31 Install operation 8 started by root:
      install activate pkg ncs6k-5.2.5.CSCuz65240-1.0.0
    Jun 02 20:19:31 Package list:
    Jun 02 20:19:31     ncs6k-5.2.5.CSCuz65240-1.0.0
    Jun 02 20:19:31     ncs6k-5.2.5.47I.CSCuy47880-0.0.4.i
    Jun 02 20:19:31     ncs6k-5.2.5.CSCux82987-1.0.0
    Jun 02 20:19:38 Install operation 8 aborted

    ------------------------------------------------------------------------------------------------------------
    Non-Reload Situation:

    RP/0/RP0/CPU0:Deploy#install deactivate ncs6k-5.2.5.CSCuz65240-1.0.0
    May 31 20:14:14 Install operation 3 started by root:
      install deactivate pkg ncs6k-5.2.5.CSCuz65240-1.0.0
    May 31 20:14:14 Package list:
    May 31 20:14:14     ncs6k-5.2.5.CSCuz65240-1.0.0
    May 31 20:14:20 Install operation will continue in the background (may or may not be displayed)

    <--- Time Lapses --->

    RP/0/RP0/CPU0:Deploy#May 31 20:15:10 Install operation 3 finished successfully

    ------------------------------------------------------------------------------------------------------------
    Reload Situation 1:

    RP/0/RP0/CPU0:Deploy#install activate ncs6k-5.2.5.CSCux82987-1.0.0
    May 31 20:17:08 Install operation 4 started by root:
      install activate pkg ncs6k-5.2.5.CSCux82987-1.0.0
    May 31 20:17:08 Package list:
    May 31 20:17:08     ncs6k-5.2.5.CSCux82987-1.0.0

    <--- Time Lapses --->

    This install operation will reboot the sdr, continue?
     [yes/no]:[yes] <Hit Enter>
    May 31 20:17:47 Install operation will continue in the background

    <--- Time Lapses --->

    RP/0/RP0/CPU0:Deploy#May 31 20:18:44 Install operation 4 finished successfully

    <--- Router Starts Reloading --->

    Connection closed by foreign host.

    Reload Situation 2:

    RP/0/RSP0/CPU0:ios#install activate id 25
    Jun 09 15:49:15 Install operation 27 started by root:
    install activate id 25
    Jun 09 15:49:15 Package list:
    Jun 09 15:49:15     asr9k-sysadmin-system-6.1.1.17-r61116I.CSCcv44444.x86_64
    Jun 09 15:49:15     asr9k-os-supp-64-3.1.0.1-r61116I.CSCxr90021.x86_64
    Jun 09 15:49:15     asr9k-base-64-4.0.0.2-r61116I.CSCxr90014.x86_64
    Jun 09 15:49:15     asr9k-sysadmin-topo-6.1.1.17-r61116I.CSCcv55555.x86_64

    This install operation will reload the sdr, continue?
    [yes/no]:[yes] <Hit Enter>
    Jun 09 15:49:26 Install operation will continue in the background
    RP/0/RSP0/CPU0:ios#

    <--- Time Lapses --->

    RP/0/RSP0/CPU0:ios#Jun 09 15:53:51 Install operation 27 finished successfully

    """
    global plugin_ctx
    plugin_ctx = ctx

    ABORTED = re.compile("aborted")

    # REBOOT_PROMP for eXR reload response:
    # This install operation will reload the sdr, continue?
    #  [yes/no]:[yes]
    # REBOOT_PROMP for NCS5K reload response:
    # This install operation will reload the system, continue?
    #  [yes/no]:[yes]

    # Seeing this message without the reboot prompt indicates a non-reload situation
    CONTINUE_IN_BACKGROUND = re.compile("Install operation will continue in the background")
    REBOOT_PROMPT = re.compile("This install operation will (?:reboot|reload) the sdr, continue")
    RELOAD_PROMPT = re.compile("This install operation will reload the system, continue")
    RUN_PROMPT = re.compile("#")
    NO_IMPACT = re.compile("NO IMPACT OPERATION")
    ERROR = re.compile(re.escape("ERROR! there was an SU/ISSU done. please perform install commit before "
                                 "proceeding with any other prepare/activate/deactivate operation"))
    NOT_START = re.compile("Could not start this install operation")
    ISSU_PROMPT = re.compile("This install operation will start the issu")
    ADMIN_RELOAD_PROMPT = re.compile("Do you want to proceed")
    ADMIN_OP_FAILED = re.compile("result Operation failed.")

    #                  0                    1              2           3          4         5          6         7         8
    events = [CONTINUE_IN_BACKGROUND, REBOOT_PROMPT, RELOAD_PROMPT, ABORTED, NO_IMPACT, RUN_PROMPT, ERROR, NOT_START, ISSU_PROMPT,
    ADMIN_RELOAD_PROMPT , ADMIN_OP_FAILED, ]
    transitions = [
        (CONTINUE_IN_BACKGROUND, [0], -1, handle_non_reload_activate_deactivate, 300),
        (REBOOT_PROMPT, [0], -1, handle_reload_activate_deactivate, 300),
        (RELOAD_PROMPT, [0], -1, handle_reload_activate_deactivate, 300),
        (NO_IMPACT, [0], -1, no_impact_warning, 60),
        (RUN_PROMPT, [0], -1, handle_non_reload_activate_deactivate, 300),
        (ABORTED, [0], -1, handle_aborted, 300),
        (ERROR, [0], -1, handle_op_after_su, 0),
        (NOT_START, [0], -1, handle_not_start, 300),
        (ISSU_PROMPT, [0], -1, handle_issu_reload, 300),
        (ADMIN_RELOAD_PROMPT, [0], -1, handle_admin_reload, 300),
        (ADMIN_OP_FAILED, [0], -1, handle_admin_op_failure, 300),

    ]

    if not ctx.run_fsm("ACTIVATE-OR-DEACTIVATE", cmd, events, transitions, timeout=300):
        ctx.error("Failed: {}".format(cmd))


def send_admin_cmd(ctx, cmd):
    ctx.send("admin")
    output = ctx.send(cmd)
    ctx.send("exit")

    return output

def match_pattern(pattern, output):
    if pattern:
        result_pass, result_fail = True, False
        if 'pass' in pattern:
            regex = re.compile("%s" %"|".join(pattern['pass']))
            result_list = regex.findall(output)
            result_pass = "^|^".join(result_list)
        if 'fail' in pattern:
            regex = re.compile("%s" %"|".join(pattern['fail']))
            result_list = regex.findall(output)
            result_fail = "^|^".join(result_list)
        if result_pass and not result_fail:
            return True, "Pattern {} matched in {}..!!!".format(pattern, output)
        else:
            return False, "Pattern {} not matched in {}!!!\n".format(pattern, output)
    else:
        return True, "Pattern unspecified. Proceeding..."

def observe_install_remove_all(ctx, cmd, prompt):
    """
    Success Condition:
    RP/0/RSP0/CPU0:vkg3#install remove inactive all
    Mar 01 16:17:13 Install operation 15 started by root:
      install remove inactive all
    Mar 01 16:17:14 Install operation will continue in the background
    RP/0/RSP0/CPU0:vkg3#Mar 01 16:17:18 Install operation 15 finished successfully

    Failed Conditions:
    RP/0/RSP0/CPU0:vkg3#install remove inactive all
    Mar 01 21:31:22 Install operation 17 started by root:
      install remove inactive all
    Mar 01 21:31:24 Install operation will continue in the background
    RP/0/RSP0/CPU0:vkg3#Mar 01 21:31:25 Install operation 17 aborted

    RP/0/RSP0/CPU0:vkg3#install remove inactive all
    Could not start this install operation. Install operation 18 is still in progress
    """
    # no op_id is returned from XR for install remove inactive
    # need to figure out the last op_id first

    cmd_show_install_log_reverse = 'show install log reverse | utility egrep "Install operation [0-9]+ started"'
    output = ctx.send(cmd_show_install_log_reverse, timeout=300)

    if 'No install operation' in output:
        op_id = 0
    else:
        result = re.search('Install operation (\d+) started', output)
        if result:
            op_id = int(result.group(1))
        else:
            log_install_errors(ctx, output)
            ctx.error("Operation ID not found by show install log reverse")
            return

    # Expected Operation ID
    op_id += 1

    oper_err = "Install operation {} aborted".format(op_id)
    oper_success = "Install operation {} finished successfully".format(op_id)
    Error1 = re.compile("Could not start this install operation. Install operation")
    Error2 = re.compile(oper_err)
    Proceed_removing = re.compile(oper_success)
    Host_prompt = re.compile(prompt)

    events = [Host_prompt, Error1, Error2, Proceed_removing]
    transitions = [
        (Error1, [0], -1, CommandError("Another install command is currently in operation",
                                       ctx._connection.hostname), 1800),
        (Error2, [0], -1, CommandError("No packages can be removed", ctx._connection.hostname), 1800),
        (Proceed_removing, [0], -1, None, 1800),
        (Host_prompt, [0], -1, None, 1800),
    ]

    if not ctx.run_fsm("Remove Inactive All", cmd, events, transitions, timeout=1800):
        ctx.error("Failed: {}".format(cmd))

    message = "Waiting the operation to continue asynchronously"
    ctx.info(message)
    ctx.post_status(message)

    last_status = None
    no_install = r"No install operation in progress"
    op_progress = r"The install operation {} is (\d+)% complete".format(op_id)
    cmd_show_install_request = "show install request"
    propeller = itertools.cycle(["|", "/", "-", "\\", "|", "/", "-", "\\"])

    finish = False
    time_tried = 0
    op_id = str(op_id)
    while not finish:
        try:
            try:
                # this is to catch the successful operation as soon as possible
                ctx.send("", wait_for_string=oper_success, timeout=20)
                finish = True
            except ctx.CommandTimeoutError:
                pass


            message = ""
            output = ctx.send(cmd_show_install_request, timeout=300)
            if op_id in output:
                result = re.search(op_progress, output)
                if result:
                    status = result.group(0)
                    message = "{} {}".format(propeller.next(), status)

                if message != last_status:
                    ctx.post_status(message)
                    last_status = message
        except (ConnectionError, ctx.CommandTimeoutError) as e:
            if time_tried > 120:
                raise e

            time_tried += 1
            time.sleep(30)

        if no_install in output:
            break

    cmd_show_install_log = "show install log {} detail".format(op_id)
    output = ctx.send(cmd_show_install_log, timeout=600)
    ctx.info(output)

    if oper_success in output:
        message = "Remove All Inactive Package(s) Successfully"
        ctx.info(message)
        ctx.post_status(message)
    else:
        ctx.error("Remove All Inactive Package(s) failed")

def wait_for_prompt(ctx):
    proceed = False
    while not proceed:
        ctx.info("checking if pending operation in progress")
        try:
            output = ctx.send(" show install request", timeout=30)
        except ctx.CommandTimeoutError:
            pass
        if "No install operation in progress" in output:
            proceed = True
        if not proceed:
            time.sleep(30)
    return

def process_save_data(ctx):
    ctx.info("Processing data to save")
    tc_id = ctx.tc_id - 1
    log_dir = ctx.log_directory
    tc_file = os.path.join(log_dir, 'tc.json')
    with open(tc_file) as fd_tc:
        data  = json.load(fd_tc)
    tc = data[tc_id]
    with open(tc_file) as fd_tc:
        tc_file_content  = fd_tc.read()
    if tc.get('save_data'):
        save_data = tc['save_data']
    else:
        return
    print save_data
    for to_save, to_replace in save_data.iteritems():
        to_save_value = getattr(ctx, to_save)
        ctx.info("Replace {} with value {}".format(to_replace , to_save_value))
        updated_content = tc_file_content.replace(to_replace, to_save_value)

    ctx.info("Writing {}".format(updated_content))

    with open(tc_file, 'w') as fd_tc:
        fd_tc.write(updated_content)

def nextlevel_processing(ctx):
    if ctx.nextlevel:
        ctx.info("In next level processing {} ".format(ctx.nextlevel))

        for cmds in ctx.nextlevel:
            shell = cmds.get("shell")
            cmd = cmds.get("command")
            pattern = cmds.get("pattern")
            if "Bash" in shell:
                cmd_list = [ "run " + c for c in cmd]
            else:
                cmd_list = cmd
            ctx.post_status("Commands {}".format(cmd_list))
            if shell == "AdminBash":
                ctx.send("admin", timeout=100)

            for cmd in cmd_list:
                cmd_out = ctx.send(cmd, timeout=200)

            if shell == "AdminBash":
                ctx.send("exit", timeout=100)

            if pattern:
                status, message = match_pattern(pattern, cmd_out)
                report_log(ctx, status, message)
                if not status:
                    ctx.error("Pattern: {} not matched in Output: {}".format(pattern, cmd_out))
    else:
        ctx.info("No next level processing required")



