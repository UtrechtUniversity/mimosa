from mimosa.components import mitigation


class MockAbstractModel:
    def __init__(self):
        self.t = [0, 1, 2, 3, 4, 5]
        self.regions = ["r1", "r2", "r3"]
        self.learning_factor = [1] * len(self.t)


def test_mac():
    m = MockAbstractModel()
    m.MAC_scaling_factor = {r: 1 for r in m.regions}
    m.MAC_gamma = 100
    m.MAC_beta = 3

    assert mitigation.MAC(0, m, 0, "r1") == 0
    assert mitigation.MAC(1, m, 0, "r1") == m.MAC_gamma
