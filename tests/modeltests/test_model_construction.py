import logging

from pyomo.environ import AbstractModel, Var

from mimosa import MIMOSA, load_params


REPLACEMENT_WARNING = "Implicitly replacing the Component attribute"


def _replacement_warnings(records):
    return [
        record.getMessage()
        for record in records
        if REPLACEMENT_WARNING in record.getMessage()
    ]


def test_pyomo_component_replacement_warning_is_detected(caplog):
    """Ensure the CI safeguard recognises Pyomo's replacement warning."""
    model = AbstractModel()
    model.duplicate = Var()

    with caplog.at_level(logging.WARNING, logger="pyomo.core"):
        model.duplicate = Var()

    assert len(_replacement_warnings(caplog.records)) == 1


def test_default_model_does_not_replace_pyomo_components(caplog):
    """Fail when a model declaration silently replaces an earlier component."""
    with caplog.at_level(logging.WARNING, logger="pyomo.core"):
        MIMOSA(load_params(), prerun=False)

    assert _replacement_warnings(caplog.records) == []
