"""
fork server method
"""

from typing import List, Tuple
import os
import socket
import sys
import fcntl
import termios
import array
import select
from . import _io, utils


def child_main(*, sock: socket.socket):
    """child for fork-server"""
    p2c_r, c2p_w = sock.makefile("rb"), sock.makefile("wb")
    _io.write_str(c2p_w, os.getcwd())
    _io.write_str_array(c2p_w, sys.argv)

    print("Open new PTY", file=sys.stderr)
    master_fd, slave_fd = os.openpty()
    print("Send PTY fd to server", file=sys.stderr)
    _send_fds(sock, b"pty", [slave_fd])
    print("Wait for server to be ready", file=sys.stderr)
    _io.read_expected(p2c_r, b"ok")
    print("Entering PTY proxy loop", file=sys.stderr)
    os.close(slave_fd)

    tcattr = termios.tcgetattr(0)
    orig_tcattr = tcattr.copy()
    try:
        # TTY raw mode (cfmakeraw)
        tcattr[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.IGNPAR | termios.PARMRK | termios.INPCK |
                       termios.ISTRIP | termios.INLCR | termios.IGNCR | termios.ICRNL | termios.IXON |
                       termios.IXANY | termios.IXOFF)
        tcattr[1] &= ~termios.OPOST
        tcattr[2] &= ~(termios.PARENB | termios.CSIZE)
        tcattr[2] |= termios.CS8
        tcattr[3] &= ~(termios.ECHO | termios.ECHOE | termios.ECHOK | termios.ECHONL | termios.ICANON |
                       termios.IEXTEN | termios.ISIG | termios.NOFLSH | termios.TOSTOP)
        tcattr[6][termios.VMIN] = 1
        tcattr[6][termios.VTIME] = 0
        termios.tcsetattr(0, termios.TCSANOW, tcattr)

        # PTY proxy
        pty = os.fdopen(master_fd, "wb")
        stdout = os.fdopen(1, "wb")
        while True:
            rl, _, _ = select.select([0, master_fd], [], [])
            if master_fd in rl:
                try:
                    buf = os.read(master_fd, 4096)
                except OSError:  # Input/output error, when closed
                    break
                if not buf:
                    break
                stdout.write(buf)
                stdout.flush()
            if 0 in rl:
                buf = os.read(0, 4096)
                if not buf:
                    break
                pty.write(buf)
                pty.flush()
    finally:
        termios.tcsetattr(0, termios.TCSANOW, orig_tcattr)
        sock.close()
    sys.exit()


def server_main(*, sock: socket.socket, modules: List[str], file_prefix: str):
    """server for fork-server"""
    server_preload(modules=modules)

    if os.fork() != 0:
        # In parent.
        # This was started when the bundled app was started for the first time,
        # thus we were given some arguments which also should be handled now.
        utils.child_run(sys.argv)
        # Leave the child alone. See below.
        return

    # See docs/pty-details.md for some background.
    # In child. Further logic here.
    # This is such that the child is not a process group leader,
    # such that os.setsid() works below.
    # Detach the TTY now.
    fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    fcntl.ioctl(fd, termios.TIOCNOTTY)
    os.close(0)
    os.dup2(os.open(file_prefix + ".stdout", os.O_CREAT | os.O_APPEND | os.O_WRONLY), 1)
    os.dup2(os.open(file_prefix + ".stderr", os.O_CREAT | os.O_APPEND | os.O_WRONLY), 2)

    # now wait for other childs
    while True:
        conn, _ = sock.accept()
        server_handle_child(conn)
        conn.close()


def server_preload(*, modules: List[str]):
    """
    Preload
    """
    import importlib

    for mod_name in modules:
        print("Import module:", mod_name)
        importlib.import_module(mod_name)


def server_handle_child(conn: socket.socket):
    """handle child for fork-server"""
    c2p_r, p2c_w = conn.makefile("rb"), conn.makefile("wb")
    cwd = _io.read_str(c2p_r)
    args = _io.read_str_array(c2p_r)
    print("Handle child:", args, file=sys.stderr)

    msg, (slave_fd,) = _recv_fds(conn, msglen=3, maxfds=1)
    assert msg == b"pty"
    print("Got PTY fd from client", file=sys.stderr)
    os.set_inheritable(slave_fd, True)
    p2c_w.write(b"ok")
    p2c_w.flush()

    pid = os.fork()
    if pid == 0:  # child:
        os.setsid()
        fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 1)
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        if slave_fd > 2:
            os.close(slave_fd)
        os.chdir(cwd)
        utils.child_run(args)
        sys.exit(0)

    # parent
    os.close(slave_fd)
    # continue, wait for potential other childs


def _send_fds(sock: socket.socket, msg: bytes, fds: List[int]):
    return sock.sendmsg([msg], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", fds))])


def _recv_fds(sock: socket.socket, msglen: int, maxfds: int) -> Tuple[bytes, List[int]]:
    fds = array.array("i")   # Array of ints
    msg, ancdata, flags, addr = sock.recvmsg(msglen, socket.CMSG_LEN(maxfds * fds.itemsize))
    for cmsg_level, cmsg_type, cmsg_data in ancdata:
        if cmsg_level == socket.SOL_SOCKET and cmsg_type == socket.SCM_RIGHTS:
            # Append data, ignoring any truncated integers at the end.
            fds.frombytes(cmsg_data[:len(cmsg_data) - (len(cmsg_data) % fds.itemsize)])
    return msg, list(fds)
