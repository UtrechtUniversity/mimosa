import pytest
import numpy as np

from mimosa.common import (
    ConcreteModel,
    Var,
    Set,
    Param,
    Any,
)
from mimosa.core.simulation import SimVar

TEST_PARAM_VALUES = {
    "region1": "str_val1",
    "region2": "str_val2",
}


@pytest.fixture
def m():
    m = ConcreteModel()
    m.t = Set(initialize=[0, 1, 2, 3])
    m.regions = Set(initialize=["region1", "region2"])
    m.var1 = Var(m.t, initialize=lambda m, t: t**2)  # Set some initial values
    m.var2 = Var(
        m.t, m.regions, initialize=lambda m, t, r: 100 * t + int(r[-1])
    )  # e.g., region1 -> 1, region2 -> 2
    m.param1 = Param(
        m.regions, initialize=lambda m, r: TEST_PARAM_VALUES[r], within=Any
    )
    return m


def test_get_and_set_values(m):

    ### Test 1: check if SimVar saves the correct values from the Pyomo object
    simvar1 = SimVar(m.var1)
    assert simvar1[2] == 4  # Initial value from var1 at t=2

    ### Test 2: check if SimVar can also set values correctly
    simvar1[2] = 10
    assert simvar1[2] == 10


def test_indexing_modes(m):

    ### Test 3: check if SimVar can handle multi-indexed variables and indexing modes
    simvar2 = SimVar(m.var2)
    # First set use_indexed = True, meaning that you can access values
    # using its index: simvar2[2, "region1"] for example
    simvar2.use_indexed = True
    assert simvar2[2, "region1"] == 201

    # Then set use_indexed = False, meaning you access values using the position of the index
    # (e.g. simvar2[0, 0], simvar2[1, 2], ...)
    simvar2.use_indexed = False
    with pytest.raises(IndexError):
        _ = simvar2[2, "region1"]  # This should raise an error now
    assert simvar2[2, 0] == 201

    # When use_indexed = False, you can still use slices:
    selection = simvar2[1:, 0]  # Get all timesteps starting at t=1 for region1
    expected = np.array([101.0, 201.0, 301.0])
    np.testing.assert_array_equal(selection, expected)


def test_simvar_param(m):

    ### Test 4: check if SimVar also works for Param objects
    simparam1 = SimVar(m.param1)
    assert simparam1[0] == TEST_PARAM_VALUES["region1"]
    assert simparam1[1] == TEST_PARAM_VALUES["region2"]

    simparam1.use_indexed = True
    assert simparam1["region1"] == TEST_PARAM_VALUES["region1"]
    assert simparam1["region2"] == TEST_PARAM_VALUES["region2"]
