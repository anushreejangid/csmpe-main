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
import re
import time
import itertools
from condoor import ConnectionError
from csmpe.core_plugins.csm_node_status_check.ios_xr.plugin_lib import parse_show_platform

install_error_pattern = re.compile("Error:    (.*)$", re.MULTILINE)


def log_install_errors(ctx, output):
    errors = re.findall(install_error_pattern, output)
    for line in errors:
        ctx.warning(line)


def watch_operation(ctx, op_id=0):
    """
    Function to keep watch on progress of operation
    and report KB downloaded.

    """
    no_install = r"There are no install requests in operation"
    op_progress = r"The operation is (\d+)% complete"
    op_download = r"(.*)KB downloaded: Download in progress"
    success = "Install operation {} completed successfully".format(op_id)

    cmd_show_install_request = "admin show install request"

    ctx.info("Watching the operation {} to complete".format(op_id))

    propeller = itertools.cycle(["|", "/", "-", "\\", "|", "/", "-", "\\"])

    output = None
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
            # on CRS, it is observed that during Add, any command typed hangs for a while
            output = ctx.send(cmd_show_install_request, timeout=300)
            if op_id in output:
                # FIXME reconsider the logic here
                result = re.search(op_progress, output)
                if result:
                    status = result.group(0)
                    message = "{} {}".format(propeller.next(), status)

                result = re.search(op_download, output)
                if result:
                    status = result.group(0)
                    message += "\r\n<br>{}".format(status)

                if message != last_status:
                    ctx.post_status(message)
                    last_status = message
        except (ConnectionError, ctx.CommandTimeoutError) as e:
            if time_tried > 2:
                raise e

            time_tried += 1
            ctx.disconnect()
            time.sleep(60)
            ctx.reconnect()

        if no_install in output:
            break

    return output


def validate_node_state(inventory):
    valid_state = [
        'IOS XR RUN',
        'PRESENT',
        'UNPOWERED',
        'READY',
        'UNPOWERED',
        'FAILED',
        'OK',
        'ADMIN DOWN',
        'DISABLED'
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
    ctx.disconnect()
    time.sleep(60)

    ctx.reconnect(max_timeout=1500)  # 25 * 60 = 1500
    timeout = 3600
    poll_time = 30
    time_waited = 0
    xr_run = "IOS XR RUN"

    cmd = "admin show platform"
    ctx.info("Waiting for all nodes to come up")
    ctx.post_status("Waiting for all nodes to come up")
    time.sleep(100)

    output = None

    while 1:
        # Wait till all nodes are in XR run state
        time_waited += poll_time
        if time_waited >= timeout:
            break

        time.sleep(poll_time)

        output = ctx.send(cmd)
        if xr_run in output:
            inventory = parse_show_platform(ctx, output)
            if validate_node_state(inventory):
                ctx.info("All nodes in desired state")
                return True

    # Some nodes did not come to run state
    ctx.error("Not all nodes have came up: {}".format(output))
    # this will never be executed
    return False


def watch_install(ctx, cmd, op_id=0):
    success_oper = r'Install operation (\d+) completed successfully'
    completed_with_failure = 'Install operation (\d+) completed with failure'
    failed_oper = r'Install operation (\d+) failed'
    failed_incr = r'incremental.*parallel'
    # restart = r'Parallel Process Restart'
    install_method = r'Install [M|m]ethod: (.*)'
    op_success = "The install operation will continue asynchronously"

    watch_operation(ctx, op_id)

    output = ctx.send("admin show install log {} detail".format(op_id))
    if re.search(failed_oper, output):
        if re.search(failed_incr, output):
            ctx.info("Retrying with parallel reload option")
            cmd += " parallel-reload"
            output = ctx.send(cmd)
            if op_success in output:
                result = re.search('Install operation (\d+) \'', output)
                if result:
                    op_id = result.group(1)
                    watch_operation(ctx, op_id)
                    output = ctx.send("admin show install log {} detail".format(op_id))
                else:
                    log_install_errors(ctx, output)
                    ctx.error("Operation ID not found")
                    return
        else:
            log_install_errors(ctx, output)
            ctx.error(output)
            return

    result = re.search(install_method, output)
    if result:
        restart_type = result.group(1).strip()
        ctx.info("{} Pending".format(restart_type))
        if restart_type == "Parallel Reload":
            if re.search(completed_with_failure, output):
                ctx.info("Install completed with failure, going for reload")
            elif re.search(success_oper, output):
                ctx.info("Install completed successfully, going for reload")
            return wait_for_reload(ctx)
        elif restart_type == "Parallel Process Restart":
            return True

    log_install_errors(ctx, output)
    return False


def install_add_remove(ctx, cmd, has_tar=False):
    message = "Waiting the operation to continue asynchronously"
    ctx.info(message)
    ctx.post_status(message)

    output = ctx.send(cmd, timeout=7200)
    result = re.search('Install operation (\d+) \'', output)
    if result:
        op_id = result.group(1)
        if has_tar is True:
            ctx.operation_id = op_id
            ctx.info("The operation {} stored".format(op_id))
    else:
        log_install_errors(ctx, output)
        ctx.error("Operation failed")
        return  # for sake of clarity

    op_success = "The install operation will continue asynchronously"
    failed_oper = r'Install operation {} failed'.format(op_id)
    if op_success in output:
        watch_operation(ctx, op_id=op_id)
        output = ctx.send("admin show install log {} detail".format(op_id))
        if re.search(failed_oper, output):
            log_install_errors(ctx, output)
            ctx.error("Operation {} failed".format(op_id))
            return  # for same of clarity

        ctx.info("Operation {} finished successfully".format(op_id))
        return  # for sake of clarity
    else:
        log_install_errors(ctx, output)
        ctx.error("Operation {} failed".format(op_id))


def install_activate_deactivate(ctx, cmd):
    message = "Waiting the operation to continue asynchronously"
    ctx.info(message)
    ctx.post_status(message)

    op_success = "The install operation will continue asynchronously"
    output = ctx.send(cmd, timeout=7200)
    result = re.search('Install operation (\d+) \'', output)
    if result:
        op_id = result.group(1)
    else:
        log_install_errors(ctx, output)
        ctx.error("Operation failed")
        return

    if op_success in output:
        success = watch_install(ctx, cmd, op_id)
        if not success:
            ctx.error("Reload or boot failure")
            return

        ctx.info("Operation {} finished successfully".format(op_id))
        return
    else:
        log_install_errors(ctx, output)
        ctx.error("Operation {} failed".format(op_id))
        return
