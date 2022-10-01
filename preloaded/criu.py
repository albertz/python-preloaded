"""
Simple CRIU wrapper
"""

import cffi


_ffi = cffi.FFI()
_ffi.cdef("""
int criu_init_opts(void);
int criu_set_images_dir_fd(int fd);
int criu_set_pid(int pid);
int criu_set_leave_running(bool leave_running);
int criu_set_tcp_established(bool tcp_established);
int criu_dump(void);
int criu_restore(void);
""")
_criu = _ffi.dlopen("libcriu.so")


def dump(checkpoint_path: str):
    """
    Dump
    """

    _criu.criu_init_opts()
    _criu.criu_set_images_dir_fd(3)
    _criu.criu_set_pid(0)
    _criu.criu_set_leave_running(True)
    _criu.criu_set_tcp_established(True)

    if _criu.criu_dump() != 0:
        raise Exception("dump failed")


def restore(checkpoint_path: str):
    """
    restore
    """
