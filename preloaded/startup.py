"""
Startup helper for preloaded bundle
"""

from __future__ import annotations
from typing import BinaryIO, List
import os
import sys
import socket

from . import _io, utils


def startup_after_criu_dump(*, p2c_r: BinaryIO):
    """
    Main entry, right after the dump.
    I.e. this is the context after restore, with the preloaded modules.
    """

    args = _io.read_str_array(p2c_r)
    utils.child_run(args)


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
    import platform
    file_prefix = sys.argv[0] + ".server." + platform.node()
    sock_name = file_prefix + ".socket"

    try:
        import faulthandler
        import signal
        faulthandler.register(signal.SIGUSR1, all_threads=True, chain=False)
    except ImportError:
        pass  # ignore

    if os.path.exists(sock_name):
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(sock_name)
        except socket.error as exc:
            print("Existing socket but can not connect:", exc, file=sys.stderr)
            os.unlink(sock_name)
        else:
            print("Existing socket, connected", file=sys.stderr)
            fork_server.child_main(sock=sock)
            return

    # Socket not found or cannot connect, start server in new process.
    print("Starting fork server", file=sys.stderr)
    c2p_r, c2p_w = os.pipe()
    os.set_inheritable(c2p_w, True)
    pid = os.fork()
    if pid == 0:  # child
        # Run the fork server.
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(sock_name)
        sock.listen()
        fork_server_pid = os.getpid()
        try:
            fork_server.server_main(
                sock=sock, modules=modules, file_prefix=file_prefix, signal_ready=os.fdopen(c2p_w, "wb"))
        finally:
            if os.getpid() == fork_server_pid:
                sock.close()
                os.unlink(sock_name)
        return

    # parent
    os.close(c2p_w)
    print("Waiting for fork server", file=sys.stderr)
    server_signal_ready = os.fdopen(c2p_r, "rb")
    _io.read_expected(server_signal_ready, b"ready")
    print("Connecting to fork server", file=sys.stderr)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(sock_name)
    print("Connected", file=sys.stderr)
    fork_server.child_main(sock=sock)
