"""
Demo for IPython.
Similar as just running `python -m IPython`.
"""

import sys
import runpy

runpy.run_module("IPython", run_name="__main__", alter_sys=True)
