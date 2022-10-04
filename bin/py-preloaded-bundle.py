#!/usr/bin/env python3

"""
Create bundle with preloaded modules.

Usage:

    py-preloaded-bundle.py <module> <module> ... -o <output-runtime-file>

    <output-runtime-file> <python-script>

Example:

    # original command:
    python my_script.py --foo bar --baz 123

    # create bundle:
    py-preloaded-bundle.py pytorch -o python-pytorch.bin

    # run with bundle, faster startup:
    ./python-pytorch.bin my_script.py --foo bar --baz 123
"""

from __future__ import annotations
from typing import BinaryIO
import argparse
import importlib
import sys
import os
import textwrap
from preloaded import criu, startup, _io


def main():
    """main entry"""
    arg_parser = argparse.ArgumentParser(
        epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    arg_parser.add_argument("modules", nargs="+", help="modules to preload")
    arg_parser.add_argument("-o", "--output", required=True, help="output runtime file")
    args = arg_parser.parse_args()

    c2p_r_fd, c2p_w_fd = os.pipe()
    p2c_r_fd, p2c_w_fd = os.pipe()
    os.set_inheritable(c2p_w_fd, True)
    os.set_inheritable(p2c_r_fd, True)
    old_pipe_ino = os.fstat(p2c_r_fd).st_ino

    with open(args.output, "w") as f:
        f.write(textwrap.dedent(f"""\
            #!/usr/bin/env python3

            import os
            from preloaded.startup import startup_restore

            if __name__ == "__main__":
                startup_restore(
                    checkpoint_path=os.path.abspath(__file__) + ".ckpt",
                    old_pipe_ino={old_pipe_ino},
                    p2c_r_fd={p2c_r_fd})
            """))
    os.chmod(args.output, 0o755)

    fork_pid = os.fork()
    if fork_pid == 0:  # child
        c2p_w = os.fdopen(c2p_w_fd, "wb")
        p2c_r = os.fdopen(p2c_r_fd, "rb")
        child_preload_and_startup(modules=args.modules, c2p_w=c2p_w, p2c_r=p2c_r)
        sys.exit()

    # parent
    os.close(c2p_w_fd)
    os.close(p2c_r_fd)
    c2p_r = os.fdopen(c2p_r_fd, "rb")
    _io.read_expected(c2p_r, b"child_ready")  # wait until child is ready

    criu.dump(args.output + ".ckpt", pid=fork_pid)
    # Successful dump should also exit the child, but anyway check waitpid, but discarding the exit code.
    os.waitpid(fork_pid, 0)
    print("Dumped executable state, created startup helper script:", args.output)


def child_preload_and_startup(*, modules: list[str], c2p_w: BinaryIO, p2c_r: BinaryIO):
    """
    Preload, dump, and then potential startup after restore
    """

    for mod_name in modules:
        print("Import module:", mod_name)
        importlib.import_module(mod_name)

    c2p_w.write(b"child_ready")  # notify
    c2p_w.flush()
    parent_cmd = _io.read_bytes(p2c_r)  # wait, get command

    # Now we should be in the restored state. The original state should have been stopped.
    if parent_cmd == b"startup_after_dump":
        startup.startup_after_dump(p2c_r=p2c_r)
        # Should not get here.
        raise Exception("startup_after_dump should not return")

    else:
        raise ValueError(f"unexpected parent_cmd {parent_cmd}")


if __name__ == '__main__':
    main()
