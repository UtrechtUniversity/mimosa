from types import SimpleNamespace

import pytest

from mimosa import MIMOSA, load_params
from mimosa.common.config.parseconfig import check_params
from mimosa.core.helpers import ComponentConfig, ModelContext


def _context(
    module="ACCREU",
    adaptation="separate",
    strategy="mitigation_then_adaptation",
    determination="analytical_optimum",
):
    return ModelContext(
        components={
            "damage": ComponentConfig(
                module=module,
                options={
                    "ACCREU_adaptation": adaptation,
                    "ACCREU_CBA_strategy": strategy,
                    "ACCREU_adaptation_determination": determination,
                },
            )
        }
    )


@pytest.mark.parametrize(
    ("module", "adaptation", "strategy", "determination", "expected"),
    [
        (
            "ACCREU",
            "separate",
            "mitigation_then_adaptation",
            "analytical_optimum",
            True,
        ),
        ("ACCREU", "combined", "joint", "solver_control", False),
        (
            "ACCREU",
            "noadaptation",
            "mitigation_then_adaptation",
            "solver_control",
            False,
        ),
        (
            "COACCH",
            "separate",
            "mitigation_then_adaptation",
            "solver_control",
            False,
        ),
    ],
)
def test_sequential_workflow_selection(
    module, adaptation, strategy, determination, expected
):
    model = MIMOSA.__new__(MIMOSA)
    model.model_context = _context(module, adaptation, strategy, determination)

    assert model._uses_sequential_accreu_cba() is expected


def test_cba_configuration_defaults_and_validation():
    params = load_params()
    options = params["model structure"]["damage module options"]

    assert options["ACCREU_CBA_strategy"] == "joint"
    assert options["ACCREU_adaptation_determination"] == "solver_control"

    for value in ["mitigation_then_adaptation", "joint"]:
        params = load_params()
        params["model structure"]["damage module options"][
            "ACCREU_CBA_strategy"
        ] = value
        assert check_params(params)["model structure"][
            "damage module options"
        ]["ACCREU_CBA_strategy"] == value

    params["model structure"]["damage module options"][
        "ACCREU_CBA_strategy"
    ] = "unknown"
    with pytest.raises(ValueError):
        check_params(params)

    for value in ["solver_control", "analytical_optimum"]:
        params = load_params()
        params["model structure"]["damage module options"][
            "ACCREU_adaptation_determination"
        ] = value
        assert check_params(params)["model structure"][
            "damage module options"
        ]["ACCREU_adaptation_determination"] == value

    params["model structure"]["damage module options"][
        "ACCREU_adaptation_determination"
    ] = "unknown"
    with pytest.raises(ValueError):
        check_params(params)


@pytest.mark.parametrize(
    ("strategy", "determination", "required"),
    [
        ("mitigation_then_adaptation", "solver_control", "analytical_optimum"),
        ("joint", "analytical_optimum", "solver_control"),
    ],
)
def test_solve_rejects_incompatible_strategy_and_determination(
    strategy, determination, required
):
    model = MIMOSA.__new__(MIMOSA)
    model.model_context = _context(
        strategy=strategy, determination=determination
    )
    model.status = "old status"
    model.solve_runtime = 10
    model.workflow_control_values = {"old": "controls"}

    with pytest.raises(ValueError, match=required):
        model.solve(verbose=False)

    assert model.status is None
    assert model.solve_runtime is None
    assert model.workflow_control_values is None


def test_sequential_workflow_copies_params_forwards_options_and_replays(monkeypatch):
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = "separate"
    options["ACCREU_adaptation_determination"] = "analytical_optimum"
    options["ACCREU_CBA_strategy"] = "mitigation_then_adaptation"

    model = MIMOSA.__new__(MIMOSA)
    model._params = params
    model.status = None
    model.workflow_control_values = None
    model.concrete_model = object()
    replay_result = object()
    calls = []

    mitigation_model = SimpleNamespace(status="ok")

    def construct_mitigation_model(stage_params):
        stage_options = stage_params["model structure"]["damage module options"]
        assert stage_params is not params
        assert stage_options["ACCREU_adaptation"] == "noadaptation"
        assert stage_options["ACCREU_CBA_strategy"] == "joint"
        assert (
            stage_options["ACCREU_adaptation_determination"]
            == "solver_control"
        )
        mitigation_model.solve = lambda **kwargs: calls.append(("solve", kwargs))
        return mitigation_model

    monkeypatch.setattr("mimosa.mimosa.MIMOSA", construct_mitigation_model)
    monkeypatch.setattr(
        model,
        "_extract_compatible_controls",
        lambda source: {"relative_abatement": {0: 0.5}},
    )
    monkeypatch.setattr(
        model,
        "run_simulation",
        lambda **controls: calls.append(("simulate", controls)) or replay_result,
    )
    model.simulator = SimpleNamespace(
        initialize_pyomo_model=lambda target, result: calls.append(
            ("initialize", target, result)
        )
    )

    model._solve_accreu_mitigation_then_adaptation(
        verbose=False, use_neos=True, neos_email="user@example.com"
    )

    assert options["ACCREU_adaptation"] == "separate"
    assert options["ACCREU_adaptation_determination"] == "analytical_optimum"
    assert options["ACCREU_CBA_strategy"] == "mitigation_then_adaptation"
    assert calls == [
        (
            "solve",
            {
                "verbose": False,
                "use_neos": True,
                "neos_email": "user@example.com",
            },
        ),
        ("simulate", {"relative_abatement": {0: 0.5}}),
        ("initialize", model.concrete_model, replay_result),
    ]
    assert model.workflow_control_values == {"relative_abatement": {0: 0.5}}
    assert model.status == "ok"


def test_sequential_workflow_rejects_fixed_carbon_budget():
    model = MIMOSA.__new__(MIMOSA)
    model._params = {"emissions": {"carbonbudget": object()}}

    with pytest.raises(ValueError, match="without a fixed carbon budget"):
        model._solve_accreu_mitigation_then_adaptation()


class _Index:
    def __init__(self, values):
        self.values = values

    def ordered_data(self):
        return self.values


class _Control:
    def __init__(self, values):
        self.values = values

    def extract_values(self):
        return self.values


def _transfer_model(controls, times=(0, 1), regions=("A",), values=None):
    values = values or {(0, "A"): 0.1, (1, "A"): 0.2}
    concrete_model = SimpleNamespace(t=_Index(times), regions=_Index(regions))
    for control in controls:
        setattr(concrete_model, control, _Control(values))
    model = MIMOSA.__new__(MIMOSA)
    model.simulator = SimpleNamespace(is_prepared=True, control_variables=controls)
    model.concrete_model = concrete_model
    return model


def test_control_transfer_validates_names_grids_and_indices():
    target = _transfer_model(["relative_abatement"])
    target.prepare_simulation = lambda: None

    values = target._extract_compatible_controls(
        _transfer_model(["relative_abatement"])
    )
    assert values == {"relative_abatement": {(0, "A"): 0.1, (1, "A"): 0.2}}

    with pytest.raises(ValueError, match="source controls"):
        target._extract_compatible_controls(_transfer_model(["other_control"]))

    with pytest.raises(ValueError, match="t indices"):
        target._extract_compatible_controls(
            _transfer_model(["relative_abatement"], times=(0, 2))
        )

    with pytest.raises(ValueError, match="its indices"):
        target._extract_compatible_controls(
            _transfer_model(["relative_abatement"], values={(0, "A"): 0.1})
        )


@pytest.mark.parametrize(
    ("determination", "expected_adaptation_controls"),
    [
        ("analytical_optimum", False),
        ("solver_control", True),
    ],
)
def test_determination_option_controls_whether_adaptation_is_a_control(
    determination, expected_adaptation_controls
):
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = "separate"
    options["ACCREU_adaptation_determination"] = determination

    model = MIMOSA(params, prerun=False)
    model.prepare_simulation()
    adaptation_controls = [
        name for name in model.simulator.control_variables if "adaptation" in name
    ]

    assert bool(adaptation_controls) is expected_adaptation_controls
