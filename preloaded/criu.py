"""
Simple CRIU wrapper
"""

import cffi


def persistent_fork():
    """
    Dump + restore
    """
    ffi = cffi.FFI()
    ffi.cdef("""
    int criu_init_opts(void);
    int criu_set_images_dir_fd(int fd);
    int criu_set_pid(int pid);
    int criu_set_leave_running(bool leave_running);
    int criu_set_tcp_established(bool tcp_established);
    int criu_dump(void);
    int criu_restore(void);
    """)
    criu = ffi.dlopen("libcriu.so")

    criu.criu_init_opts()
    criu.criu_set_images_dir_fd(3)
    criu.criu_set_pid(0)
    criu.criu_set_leave_running(True)
    criu.criu_set_tcp_established(True)

    if criu.criu_dump() != 0:
        raise Exception("dump failed")
    if criu.criu_restore() != 0:
        raise Exception("restore failed")

