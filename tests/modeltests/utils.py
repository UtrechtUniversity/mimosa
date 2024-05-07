import sys
import os
import warnings


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mimosa.common.utils import MimosaSolverWarning


def exec_run(filename):
    """Filename is relative to the variable "/tests/"."""
    _locals = locals()
    filename = os.path.join(os.path.dirname(__file__), "../runs/run_base.py")
    with open(filename, encoding="utf-8") as file:
        exec(file.read(), globals(), _locals)
    return _locals
