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
    py-preloaded-bundle.py pytorch -o python-pytorch

    # run with bundle, faster startup:
    ./python-pytorch my_script.py --foo bar --baz 123
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

    c2p_r, c2p_w = os.pipe()
    p2c_r, p2c_w = os.pipe()
    os.set_inheritable(c2p_w, True)
    os.set_inheritable(p2c_r, True)
    fork_pid = os.fork()
    if fork_pid == 0:  # child
        c2p_w = os.fdopen(c2p_w, "wb")
        p2c_r = os.fdopen(p2c_r, "rb")
        child_preload_and_startup(modules=args.modules, output=args.output, c2p_w=c2p_w, p2c_r=p2c_r)
        p2c_r.read(1)  # block, wait
        sys.exit()

    # parent
    c2p_r = os.fdopen(c2p_r, "rb")
    p2c_w = os.fdopen(p2c_w, "wb")
    _io.read_expected(c2p_r, b"child_ready")  # wait until child is ready
    criu.dump(args.output + ".ckpt", pid=fork_pid)
    _io.write_bytes(p2c_w, b"exit_from_bundle_exec_creator")  # notify
    p, res = os.waitpid(fork_pid, 0)
    assert p == fork_pid and res == 0, f"exit code {res} from pid {p}, child pip {fork_pid}"


def child_preload_and_startup(modules: list[str], output: str, *, c2p_w: BinaryIO, p2c_r: BinaryIO):
    """
    Preload, dump, and then potential startup after restore
    """

    for mod_name in modules:
        print("Import module:", mod_name)
        importlib.import_module(mod_name)

    with open(output, "w") as f:
        f.write(textwrap.dedent(f"""\
            #!/usr/bin/env python3
            
            import os
            from preloaded.startup import startup_restore
            
            if __name__ == "__main__":
                startup_restore(
                    checkpoint_path=os.path.absname(__file__) + ".ckpt",
                    c2p_w={c2p_w.fileno()},
                    p2c_r={p2c_r.fileno()})
            """))
    os.chmod(output, 0o755)
    
    c2p_w.write(b"child_ready")  # notify
    parent_cmd = _io.read_bytes(p2c_r)  # wait, get command

    # Now we are here either from the py-preloaded-bundle original call, or from the restore.
    # This is like a persistent fork.
    if parent_cmd == b"exit_from_bundle_exec_creator":
        # In original py-preloaded-bundle call.
        print("Created executable", output)

    elif parent_cmd == b"startup_after_dump":
        startup.startup_after_dump(p2c_r=p2c_r)

    else:
        raise ValueError(f"unexpected parent_cmd {parent_cmd}")


if __name__ == '__main__':
    main()
