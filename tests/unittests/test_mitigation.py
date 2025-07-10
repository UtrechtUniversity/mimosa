import pytest
import numpy as np

from mimosa.components import mitigation
from mimosa.common import trapezoid


class MockAbstractModel:
    def __init__(self):
        self.t = [0, 1, 2, 3, 4, 5]
        self.regions = ["r1", "r2", "r3"]
        self.learning_factor = [1] * len(self.t)


@pytest.fixture
def m():
    model = MockAbstractModel()
    model.MAC_scaling_factor = {r: 1 for r in model.regions}
    model.MAC_SSP_calibration_factor = {t: 1 for t in model.t}
    model.MAC_gamma = 100
    model.MAC_beta = 3
    return model


def test_mac(m):
    # Zero mitigation should give zero carbon price:
    assert mitigation.MAC(0, m, 0, "r1") == 0

    # Backstop technology (100% reduction) should give the calibration
    # value gamma as carbon price
    assert mitigation.MAC(1, m, 0, "r1") == m.MAC_gamma


@pytest.mark.parametrize("a_end", [0.3, 0.7, 1, 1.5])
def test_area_under_mac(a_end, request):
    m = request.getfixturevalue("m")

    # Zero mitigation should give zero abatement costs
    assert mitigation.AC(0, m, 0, "r1") == 0

    # Test if AC is equal to the integral of MAC:
    a_values = np.linspace(0, a_end, 500)
    mac_values = mitigation.MAC(a_values, m, 0, "r1")
    integral_mac = trapezoid(mac_values, x=a_values)

    abatement_costs = mitigation.AC(a_end, m, 0, "r1")

    # Since integral_mac is a numerical approximation, test if
    # `integral_mac` is within 0.1% of `abatement_costs`
    assert integral_mac == pytest.approx(abatement_costs, 0.001 * abatement_costs)
