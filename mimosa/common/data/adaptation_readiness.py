"""Load the adaptation-readiness data distributed with MIMOSA."""

from pathlib import Path

import pandas as pd


def load_adaptation_readiness() -> pd.DataFrame:
    """Return the packaged adaptation-readiness table.

    The table is indexed by ``SSP`` and ``Region``. Calendar-year columns retain
    their string labels, as with ``pandas.read_csv``. Each call returns a new
    table, independent of the current working directory. Data is read only when
    this function is called.

    Example:
        ```python
        from mimosa import load_adaptation_readiness

        readiness = load_adaptation_readiness()
        factor = readiness.loc[("SSP1", "CAN"), "2030"]
        ```
    """
    path = Path(__file__).resolve().parents[2] / "inputdata/data/adaptation_readiness.csv"
    return pd.read_csv(path).set_index(["SSP", "Region"])
