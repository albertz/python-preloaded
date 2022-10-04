"""
Generic utils
"""

from typing import Optional
import os


def which(program: str) -> Optional[str]:
    """
    Finds `program` in the directories of the PATH env var.

    :param program: e.g. "criu"
    :return: full path, e.g. "/usr/bin/criu", or None
    """
    if "/" in program:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(":"):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def is_exe(path: str) -> bool:
    """
    Checks if `path` is an executable file.
    """
    return os.path.isfile(path) and os.access(path, os.X_OK)
