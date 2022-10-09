"""
Startup helper for preloaded bundle
"""

from __future__ import annotations
from typing import BinaryIO, List
import os
import sys
import runpy
import socket

from . import _io


def startup_after_criu_dump(*, p2c_r: BinaryIO):
    """
    Main entry, right after the dump.
    I.e. this is the context after restore, with the preloaded modules.
    """

    sys.argv = _io.read_str_array(p2c_r)
    runpy.run_path(sys.argv[0], run_name="__main__")


def startup_restore_criu(*, checkpoint_path: str, p2c_r_fd: int, old_pipe_ino: int):
    """main entry, prepare restore"""
    from . import criu

    p2c_r_new_fd, p2c_w_fd = os.pipe()
    os.dup2(p2c_r_new_fd, p2c_r_fd, inheritable=True)
    os.close(p2c_r_new_fd)

    child_pid = os.fork()
    if child_pid == 0:  # child
        criu.restore(checkpoint_path, p2c_r_fd=p2c_r_fd, old_pipe_ino=old_pipe_ino)
        raise Exception("Should not return from criu.restore()")

    # parent
    os.close(p2c_r_fd)
    p2c_w = os.fdopen(p2c_w_fd, "wb")
    _io.write_bytes(p2c_w, b"startup_after_dump")
    _io.write_str_array(p2c_w, sys.argv)
    p, res = os.waitpid(child_pid, 0)
    assert p == child_pid, f"exit code {res} from pid {p}, child pip {child_pid}"
    sys.exit(res)


def startup_via_fork_server(*, modules: List[str]):
    """fork server method"""
    from . import fork_server
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock_name = sys.argv[0] + ".socket"
    if os.path.exists(sock_name):
        try:
            sock.connect(sock_name)
        except socket.error as exc:
            print("Existing socket but can not connect:", exc, file=sys.stderr)
            os.unlink(sock_name)
        else:
            print("Existing socket, connected", file=sys.stderr)
            fork_server.child_main(sock=sock)
            return

    sock.bind(sock_name)
    sock.listen()
    fork_server.server_main(sock=sock, modules=modules)
