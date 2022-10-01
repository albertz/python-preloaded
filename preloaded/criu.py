"""
Simple CRIU wrapper
"""

import subprocess


def dump(checkpoint_path: str, pid: int):
    """
    Dump
    """
    subprocess.check_call(["criu", "dump", "-t", str(pid)])


def restore(checkpoint_path: str):
    """
    restore
    """
