"""
fork server method
"""
import os
from typing import List
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

    # See docs/pty-details.md for some background.
    if os.fork() != 0:
        # In parent, exit now. This is such that the child will be reparented.
        return
    # In child, but parent will exit soon.
    # Detach the TTY now.
    fcntl.ioctl(0, termios.TIOCNOTTY)
    os.close(0)
    os.dup2(os.open(sys.argv[0] + ".server.stdout", os.O_WRONLY), 1)
    os.dup2(os.open(sys.argv[0] + ".server.stderr", os.O_WRONLY), 2)

    # This was started when the bundled app was started for the first time,
    # thus we were given some arguments which also should be handled now.
    server_handle_child(sys.argv)

    # now wait for other childs
    while True:
        conn, _ = sock.accept()
        c2p_r, p2c_w = conn.makefile("rb"), conn.makefile("wb")
        args = _io.read_str_array(c2p_r)
        server_handle_child(args)
        conn.close()


def server_preload(*, modules: List[str]):
    """
    Preload
    """
    import importlib

    for mod_name in modules:
        print("Import module:", mod_name)
        importlib.import_module(mod_name)


def server_handle_child(args: List[str]):
    """handle child for fork-server"""
    # TODO...
    print("Handle child:", args, file=sys.stderr)
