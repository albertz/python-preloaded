"""
fork server method
"""
from typing import List
import os
import runpy
import socket
import sys
import fcntl
import termios
from . import _io


def child_main(*, sock: socket.socket):
    """child for fork-server"""
    p2c_r, c2p_w = sock.makefile("rb"), sock.makefile("wb")
    _io.write_str_array(c2p_w, sys.argv)
    # TODO handle pty proxy...
    sock.close()
    sys.exit()


def server_main(*, sock: socket.socket, modules: List[str]):
    """server for fork-server"""
    server_preload(modules=modules)

    if os.fork() != 0:
        # In parent.
        # This was started when the bundled app was started for the first time,
        # thus we were given some arguments which also should be handled now.
        child_run(sys.argv)
        # Leave the child alone. See below.
        return

    # See docs/pty-details.md for some background.
    # In child. Further logic here.
    # This is such that the child is not a process group leader,
    # such that os.setsid() works below.
    # Detach the TTY now.
    fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    fcntl.ioctl(fd, termios.TIOCNOTTY)
    os.setsid()
    os.close(0)
    os.dup2(os.open(sys.argv[0] + ".server.stdout", os.O_CREAT|os.O_APPEND|os.O_WRONLY), 1)
    os.dup2(os.open(sys.argv[0] + ".server.stderr", os.O_CREAT|os.O_APPEND|os.O_WRONLY), 2)

    # now wait for other childs
    while True:
        conn, _ = sock.accept()
        c2p_r, p2c_w = conn.makefile("rb"), conn.makefile("wb")
        args = _io.read_str_array(c2p_r)
        server_handle_child(conn, args)
        conn.close()


def server_preload(*, modules: List[str]):
    """
    Preload
    """
    import importlib

    for mod_name in modules:
        print("Import module:", mod_name)
        importlib.import_module(mod_name)


def server_handle_child(conn: socket.socket, args: List[str]):
    """handle child for fork-server"""
    # TODO...
    print("Handle child:", args, file=sys.stderr)

    (master_fd, slave_fd) = os.openpty()


def child_run(args: List[str]):
    """run passed args"""
    sys.modules.pop("__main__", None)  # make sure it is reloaded
    # args[0] should be the bundled Python script
    sys.argv = args[1:]
    if not sys.argv:
        import code
        code.interact()
    else:
        runpy.run_path(sys.argv[0], run_name="__main__")
