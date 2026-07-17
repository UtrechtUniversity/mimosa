import pytest

from tests.modeltests.utils import exec_run, read_output, SimulationObjectModel


pytestmark = [pytest.mark.documentation, pytest.mark.simulation]


@pytest.fixture(scope="module")
def script_output():
    """Run the prescribed-control example shown in the simulation guide."""
    return exec_run("runs/run_simulation.py")


def test_documented_simulation_runs_and_saves_output(script_output):
    """The documented simulation should return results and write a readable CSV."""
    assert isinstance(script_output["simulation"], SimulationObjectModel)
    read_output(script_output["model"], simulation=True)
