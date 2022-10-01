"""
Startup helper for preloaded bundle
"""

from __future__ import annotations
from typing import BinaryIO
import os
import sys
import runpy

from . import criu


def startup_after_dump(*, pipe_read_end_fd: int):
    """
    Main entry, right after the dump.
    I.e. this is the context after restore, with the preloaded modules.
    """

    pipe_read_end = os.fdopen(pipe_read_end_fd, "rb")
    sys.argv = _read_str_array(pipe_read_end)
    runpy.run_path(sys.argv[0], run_name="__main__")


def startup_restore(*, checkpoint_path: str, pipe_write_end_fd: int):
    """main entry, prepare restore"""

    pipe_write_end = os.fdopen(pipe_write_end_fd, "wb")
    _write_str_array(pipe_write_end, sys.argv)

    criu.restore(checkpoint_path)


def _write_int(f: BinaryIO, data: int):
    f.write(data.to_bytes(4, "little"))


def _read_int(f: BinaryIO) -> int:
    return int.from_bytes(f.read(4), "little")


def _write_str(f: BinaryIO, data: str):
    _write_bytes(f, data.encode("utf8"))


def _read_str(f: BinaryIO) -> str:
    return _read_bytes(f).decode("utf8")


def _write_bytes(f: BinaryIO, data: bytes):
    f.write(len(data).to_bytes(4, "little"))
    f.write(data)


def _read_bytes(f: BinaryIO) -> bytes:
    data_len = _read_int(f)
    return f.read(data_len)


def _write_str_array(f: BinaryIO, data: list[str]):
    _write_int(f, len(data))
    for item in data:
        _write_str(f, item)


def _read_str_array(f: BinaryIO) -> list[str]:
    data_len = _read_int(f)
    return [_read_str(f) for _ in range(data_len)]
