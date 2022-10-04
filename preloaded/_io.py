"""
Simple IO helpers
"""

from __future__ import annotations
from typing import BinaryIO


def write_int(f: BinaryIO, data: int):
    f.write(data.to_bytes(4, "little"))
    f.flush()


def read_int(f: BinaryIO) -> int:
    return int.from_bytes(f.read(4), "little")


def write_str(f: BinaryIO, data: str):
    write_bytes(f, data.encode("utf8"))


def read_str(f: BinaryIO) -> str:
    return read_bytes(f).decode("utf8")


def write_bytes(f: BinaryIO, data: bytes):
    f.write(len(data).to_bytes(4, "little"))
    f.write(data)
    f.flush()


def read_bytes(f: BinaryIO) -> bytes:
    data_len = read_int(f)
    return f.read(data_len)


def write_str_array(f: BinaryIO, data: list[str]):
    write_int(f, len(data))
    for item in data:
        write_str(f, item)


def read_str_array(f: BinaryIO) -> list[str]:
    data_len = read_int(f)
    return [read_str(f) for _ in range(data_len)]


def read_expected(f: BinaryIO, expected: bytes):
    res = f.read(len(expected))
    assert res == expected, f"Expected {expected!r}, got {res!r}"
