import json
from types import SimpleNamespace

import numpy as np
import pytest

from mimosa.export.save import save_output
from mimosa.mimosa import MIMOSA


def test_solve_stores_wall_clock_runtime(monkeypatch):
    model = MIMOSA.__new__(MIMOSA)
    model.concrete_model = object()
    model.solver = SimpleNamespace(
        solve_ipopt=lambda concrete_model, **kwargs: SimpleNamespace(
            solver=SimpleNamespace(status="ok")
        )
    )
    model.status = None
    model.solve_runtime = None
    model.workflow_control_values = None
    monkeypatch.setattr(model, "_uses_sequential_accreu_cba", lambda: False)

    timer_values = iter([100.0, 112.345])
    monkeypatch.setattr(
        "mimosa.common.utils.time.perf_counter", lambda: next(timer_values)
    )

    model.solve(verbose=False)

    assert model.solve_runtime == pytest.approx(12.345)


def test_failed_resolve_clears_previous_runtime(monkeypatch):
    model = MIMOSA.__new__(MIMOSA)
    model.concrete_model = object()

    def fail_to_solve(concrete_model, **kwargs):
        raise RuntimeError("solver failed")

    model.solver = SimpleNamespace(solve_ipopt=fail_to_solve)
    model.status = "ok"
    model.solve_runtime = 12.345
    model.workflow_control_values = {"old": "values"}
    monkeypatch.setattr(model, "_uses_sequential_accreu_cba", lambda: False)
    monkeypatch.setattr("mimosa.common.utils.time.perf_counter", lambda: 100.0)

    with pytest.raises(RuntimeError, match="solver failed"):
        model.solve(verbose=False)

    assert model.status is None
    assert model.solve_runtime is None
    assert model.workflow_control_values is None


def test_runtime_is_numeric_top_level_export_metadata(tmp_path):
    model = SimpleNamespace(
        t=[],
        year=lambda time_points: np.asarray(time_points),
    )
    params = {"example setting": 42}

    save_output(
        [],
        params,
        model,
        "run",
        folder=str(tmp_path),
        runtime=12.3456,
    )

    with open(tmp_path / "run.csv.params.json") as param_file:
        exported = json.load(param_file)

    assert exported["Runtime (seconds)"] == 12.35
    assert isinstance(exported["Runtime (seconds)"], float)
    assert "Runtime (seconds)" not in params


def test_runtime_is_omitted_when_no_solve_completed(tmp_path):
    model = SimpleNamespace(
        t=[],
        year=lambda time_points: np.asarray(time_points),
    )

    save_output([], {}, model, "run", folder=str(tmp_path))

    with open(tmp_path / "run.csv.params.json") as param_file:
        exported = json.load(param_file)

    assert "Runtime (seconds)" not in exported


def test_simulation_stores_its_own_wall_clock_runtime(monkeypatch):
    simulation = SimpleNamespace()
    model = MIMOSA.__new__(MIMOSA)
    model._params = {"example setting": 42}
    model.simulator = SimpleNamespace(
        is_prepared=True,
        run=lambda **kwargs: simulation,
    )
    timer_values = iter([20.0, 23.456])
    monkeypatch.setattr("mimosa.mimosa.time.perf_counter", lambda: next(timer_values))

    result = model.run_simulation(relative_abatement=0)

    assert result is simulation
    assert result.runtime == pytest.approx(3.456)
    assert result.params == model._params


def test_save_simulation_exports_that_simulation_runtime(monkeypatch):
    captured = {}
    model = MIMOSA.__new__(MIMOSA)
    model._params = {"example setting": 42}
    model.last_saved_simulation_filename = None
    simulation = SimpleNamespace(
        runtime=7.891,
        all_vars_for_export=lambda: [],
    )

    def capture_save(*args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("mimosa.mimosa.save_output", capture_save)

    model.save_simulation(simulation, "simulation")

    assert captured["scenario_type"] == "simulation"
    assert captured["runtime"] == pytest.approx(7.891)


def test_save_simulation_uses_parameters_from_the_simulation(monkeypatch):
    captured = {}
    model = MIMOSA.__new__(MIMOSA)
    model._params = {"model": "parameters"}
    model.last_saved_simulation_filename = None
    simulation = SimpleNamespace(
        params={"simulation": "parameters"},
        runtime=1.0,
        all_vars_for_export=lambda: [],
    )

    monkeypatch.setattr(
        "mimosa.mimosa.save_output",
        lambda variables, params, *args, **kwargs: captured.update(params=params),
    )

    model.save_simulation(simulation, "simulation")

    assert captured["params"] == {"simulation": "parameters"}
