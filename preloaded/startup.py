"""
Startup helper for preloaded bundle
"""

from __future__ import annotations
from typing import BinaryIO
import os
import sys
import runpy

from . import criu, _io


def startup_after_dump(*, p2c_r: BinaryIO):
    """
    Main entry, right after the dump.
    I.e. this is the context after restore, with the preloaded modules.
    """

    sys.argv = _io.read_str_array(p2c_r)
    runpy.run_path(sys.argv[0], run_name="__main__")


def startup_restore(*, checkpoint_path: str, c2p_w: int, p2c_r: int):
    """main entry, prepare restore"""

    c2p_w = os.fdopen(c2p_w, "wb")
    _io.write_str_array(c2p_w, sys.argv)

    criu.restore(checkpoint_path)
