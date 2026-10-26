import pandas as pd
import pytest

from mimosa import load_adaptation_readiness


def test_readiness_loads_packaged_data_from_another_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    readiness = load_adaptation_readiness()

    assert isinstance(readiness, pd.DataFrame)
    assert readiness.index.names == ["SSP", "Region"]
    assert readiness.index.is_unique
    assert "2020" in readiness.columns and "2150" in readiness.columns
    assert readiness.loc[("SSP1", "CAN"), "2030"] == pytest.approx(0.754723035722993)
    assert readiness.notna().all().all()
    assert ((readiness >= 0) & (readiness <= 1)).all().all()


def test_readiness_calls_return_independent_tables():
    first = load_adaptation_readiness()
    expected = first.loc[("SSP1", "CAN"), "2030"]
    first.loc[("SSP1", "CAN"), "2030"] = -1

    second = load_adaptation_readiness()

    assert second.loc[("SSP1", "CAN"), "2030"] == expected
