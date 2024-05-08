import pandas as pd
import os

from mimosa.common.utils import MimosaSolverWarning
from mimosa.common import SolverStatus


def exec_run(filename):
    """Filename is relative to the variable "/tests/"."""
    _locals = locals()
    filename = os.path.join(os.path.dirname(__file__), "../", filename)
    with open(filename, encoding="utf-8") as file:
        exec(file.read(), globals(), _locals)
    return _locals


def read_output(model=None, filename=None):
    if model is None and filename is None:
        raise ValueError("Either model or filename must be provided.")

    if model is not None:
        filename = model.last_saved_filename
        assert filename is not None

    # Read output file
    output_df = pd.read_csv(f"output/{filename}.csv")
    assert len(output_df) > 0

    for col in ["Variable", "Region", "Unit"]:
        assert col in output_df.columns

    return output_df.set_index(["Variable", "Region"])
