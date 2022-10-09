"""
Generic utils
"""

from typing import Optional, List
import sys
import os
import runpy


def child_run(args: List[str]):
    """run passed args"""
    sys.modules.pop("__main__", None)  # make sure it is reloaded
    # args[0] should be the bundled Python script
    sys.argv = args[1:]
    if not sys.argv:
        import code
        code.interact()
    else:
        script_path = os.path.realpath(sys.argv[0])
        sys.path.insert(0, os.path.dirname(script_path))
        runpy.run_path(script_path, run_name="__main__")


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
