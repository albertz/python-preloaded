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

import argparse
import importlib
import os
import textwrap
from preloaded import criu
from preloaded import startup


def main():
    """main entry"""
    arg_parser = argparse.ArgumentParser(
        epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    arg_parser.add_argument("modules", nargs="+", help="modules to preload")
    arg_parser.add_argument("-o", "--output", required=True, help="output runtime file")
    args = arg_parser.parse_args()

    for mod_name in args.modules:
        print("Import module:", mod_name)
        importlib.import_module(mod_name)

    pipe_read_end_fd, pipe_write_end_fd = os.pipe()
    unique_run_state_id = get_unique_run_state_id()

    with open(args.output, "w") as f:
        f.write(textwrap.dedent(f"""\
            #!/usr/bin/env python3
            
            import os
            from preloaded.startup import startup_restore
            
            if __name__ == "__main__":
                startup_restore(
                    checkpoint_path=os.path.absname(__file__) + ".ckpt",
                    pipe_read_end_fd={pipe_read_end_fd},
                    pipe_write_end_fd={pipe_write_end_fd})
            """))
    os.chmod(args.output, 0o755)

    criu.dump(args.output + ".ckpt")
    # Now we are here either from the py-preloaded-bundle original call, or from the restore.
    # This is like a persistent fork.
    if unique_run_state_id == get_unique_run_state_id():
        # In original py-preloaded-bundle call.
        print("Created executable", args.output)

    else:
        startup.startup_after_dump(pipe_read_end_fd=pipe_read_end_fd)


def get_unique_run_state_id() -> object:
    """
    Returns sth which is the same when this is the same run,
    but different when this is a new run.
    For example the pid might be different.
    """
    # TODO extend this...
    return os.getpid()


if __name__ == '__main__':
    main()
