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
    monkeypatch.setattr("mimosa.common.utils.time.perf_counter", lambda: 100.0)

    with pytest.raises(RuntimeError, match="solver failed"):
        model.solve(verbose=False)

    assert model.status is None
    assert model.solve_runtime is None


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
        solve_runtime=12.345,
    )

    with open(tmp_path / "run.csv.params.json") as param_file:
        exported = json.load(param_file)

    assert exported["Runtime (seconds)"] == pytest.approx(12.345)
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
