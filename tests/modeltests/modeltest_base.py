import os
import warnings
import pytest

warnings.filterwarnings("error")

import utils

try:
    variables = utils.exec_run("runs/run_base.py")
    print(variables["model1"])

except utils.MimosaSolverWarning as e:
    print("========== WARNING HERE ==========")
    print(e)
