import os
import runpy
import pandas as pd
import numpy as np

from mimosa.common.utils import MimosaSolverWarning
from mimosa.common import SolverStatus, value
from mimosa.core.simulation import SimulationObjectModel


def exec_run(filename):
    """Filename is relative to the variable "/tests/"."""
    filename = os.path.join(os.path.dirname(__file__), "../", filename)
    _globals = runpy.run_path(filename)
    return _globals


def read_output(model=None, filename=None, simulation=False):
    if model is None and filename is None:
        raise ValueError("Either model or filename must be provided.")

    if model is not None:
        filename = (
            model.last_saved_simulation_filename
            if simulation
            else model.last_saved_filename
        )
        assert filename is not None

    # Read output file
    output_df = pd.read_csv(f"output/{filename}.csv")
    assert len(output_df) > 0

    for col in ["Variable", "Region", "Unit"]:
        assert col in output_df.columns

    return output_df.set_index(["Variable", "Region"])


def assert_saved_regional_output(
    model, variables, simulation=None, saved_simulation=None, rtol=1e-5, atol=1e-9
):
    """Compare finite saved regional series with their model or simulation values.

    CSV output is rounded to six significant digits.
    """
    if saved_simulation is None:
        saved_simulation = simulation is not None
    output = read_output(model, simulation=saved_simulation)
    result = model.concrete_model if simulation is None else simulation
    regions = list(result.regions)
    years = [str(int(result.year(t))) for t in result.t]
    assert set(output.loc["regional_emissions"].index) == set(regions)
    for variable in variables:
        saved = output.loc[variable, years].loc[regions].to_numpy(dtype=float)
        expected = np.array([
            [value(getattr(result, variable)[t, region]) for t in result.t]
            for region in regions
        ])
        assert np.isfinite(saved).all()
        np.testing.assert_allclose(saved, expected, rtol=rtol, atol=atol)
