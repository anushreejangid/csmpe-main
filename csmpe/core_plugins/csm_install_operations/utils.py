import sys
import importlib


class ServerType:
    TFTP_SERVER = 'TFTP'
    FTP_SERVER = 'FTP'
    SFTP_SERVER = 'SFTP'
    LOCAL_SERVER = 'LOCAL'


def import_module(module, path=None):
    if path is not None:
        sys.path.append(path)
    try:
        return importlib.import_module(module)
    except:
        return None


def concatenate_dirs(dir1, dir2):
    """
    Appends dir2 to dir1. It is possible that either/both dir1 or/and dir2 is/are None
    """
    result_dir = dir1 if dir1 is not None and len(dir1) > 0 else ''
    if dir2 is not None and len(dir2) > 0:
        if len(result_dir) == 0:
            result_dir = dir2
        else:
            result_dir += '/' + dir2

    return result_dir


def is_empty(obj):
    """
    These conditions are considered empty
       s = [], s = None, s = '', s = '    ', s = 'None'
    """
    if isinstance(obj, str):
        obj = obj.replace('None', '').strip()

    if obj:
        return False

    return True


def update_device_info_udi(ctx):
    # _update_device_info() and _update_udi() are removed in condoor-ng
    # ctx._connection._update_device_info()
    # ctx._connection._update_udi()
    ctx._csm.save_data("device_info", ctx._connection.device_info)
    ctx._csm.save_data("udi", ctx._connection.udi)
