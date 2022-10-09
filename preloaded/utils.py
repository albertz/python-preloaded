"""
Generic utils
"""

from typing import Optional, List
import sys
import os


def child_run(args: List[str]):
    """run passed args"""
    import runpy
    import types
    import builtins as builtin_mod

    # make sure we have a fresh __main__
    sys.modules.pop("__main__", None)
    # Partly copied from IPython.
    new_main_module = types.ModuleType(
        "__main__", doc="Automatically created __main__ module by python-preloaded")
    # We must ensure that __builtin__ (without the final 's') is always
    # available and pointing to the __builtin__ *module*.  For more details:
    # http://mail.python.org/pipermail/python-dev/2001-April/014068.html
    new_main_module.__dict__.setdefault('__builtin__', builtin_mod)
    new_main_module.__dict__.setdefault('__builtins__', builtin_mod)
    sys.modules["__main__"] = new_main_module

    # args[0] should be the bundled Python script
    sys.argv = args[1:]
    if not sys.argv:
        import code
        code.interact()
    elif sys.argv[0] in ["-h", "--help"]:
        print(f"Usage: {args[0]} [-c cmd | -m mod | file | -] [arg] ...")
    elif sys.argv[0] == "-m":
        sys.argv = sys.argv[1:]
        assert sys.argv, "missing module name after -m"
        runpy.run_module(sys.argv[0], run_name="__main__", alter_sys=True)
    elif sys.argv[0] == "-c":
        assert len(sys.argv) == 2, f"expect exactly one arg after -c but got args {sys.argv}"
        exec(sys.argv[1])
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
