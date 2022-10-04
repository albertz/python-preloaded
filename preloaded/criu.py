"""
Simple CRIU wrapper
"""

import os
import subprocess
from . import utils


def dump(checkpoint_path: str, pid: int):
    """
    Dump
    """
    os.makedirs(checkpoint_path, exist_ok=True)
    subprocess.check_call(["sudo", "criu", "dump", "-t", str(pid), "-D", checkpoint_path, "--shell-job"])


def restore(checkpoint_path: str, *, p2c_r_fd: int, old_pipe_ino: int):
    """
    restore. does not return when successful
    """
    criu_bin = utils.which("criu")
    if not criu_bin:
        raise Exception("Cannot find criu binary in PATH")
    os.execl(
        criu_bin,
        criu_bin, "restore",
        "-D", checkpoint_path,
        "--inherit-fd", f"fd[{p2c_r_fd}]:pipe:[{old_pipe_ino}]")
