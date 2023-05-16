"""
Simple IO helpers
"""

from __future__ import annotations
from typing import Union, BinaryIO
import io


IO = Union[BinaryIO, io.RawIOBase]


def write_int(f: IO, data: int):
    f.write(data.to_bytes(4, "little"))
    f.flush()


def read_int(f: IO) -> int:
    return int.from_bytes(f.read(4), "little")


def write_str(f: IO, data: str):
    write_bytes(f, data.encode("utf8"))


def read_str(f: IO) -> str:
    return read_bytes(f).decode("utf8")


def write_bytes(f: IO, data: bytes):
    f.write(len(data).to_bytes(4, "little"))
    f.write(data)
    f.flush()


def read_bytes(f: IO) -> bytes:
    data_len = read_int(f)
    return f.read(data_len)


def write_str_array(f: IO, data: list[str]):
    write_int(f, len(data))
    for item in data:
        write_str(f, item)


def read_str_array(f: IO) -> list[str]:
    data_len = read_int(f)
    return [read_str(f) for _ in range(data_len)]


def read_expected(f: IO, expected: bytes):
    res = f.read(len(expected))
    assert res == expected, f"Expected {expected!r}, got {res!r}"
