"""Compatibility of MIMOSA's parameter factory with native Pyomo components."""

from dataclasses import FrozenInstanceError

import pytest
from pyomo.environ import (
    AbstractModel,
    Any,
    ConcreteModel,
    Constraint,
    NonNegativeReals,
    Param as NativeParam,
    Set,
    Var,
    units,
    value,
)

from mimosa.common import (
    Param,
    PyomoParam,
    SourcedValue,
    get_all_time_dependent_params,
)
from mimosa.core.simulation.objects import SimulationObjectModel


@pytest.mark.parametrize("constructor", [Param, NativeParam])
def test_plain_initialization_and_defaults_retain_pyomo_behavior(constructor):
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.scalar = constructor(initialize=3.0, doc="A normal description")
    model.indexed = constructor(model.t, initialize={0: 2.0}, default=5.0)
    model.derived = constructor(
        model.t, initialize=lambda m, t: m.scalar * m.indexed[t]
    )
    model.default_only = constructor(default=7.0)
    model.empty = constructor()
    model.flag = constructor(initialize=False, within=Any)
    model.null = constructor(initialize=None, within=Any)

    assert value(model.scalar) == 3.0
    assert model.scalar.doc == "A normal description"
    assert model.indexed.extract_values() == {0: 2.0, 1: 5.0}
    assert model.derived.extract_values() == {0: 6.0, 1: 15.0}
    assert value(model.default_only) == 7.0
    with pytest.raises(ValueError, match="undefined"):
        value(model.empty)
    assert value(model.flag) is False
    assert value(model.null, exception=False) is None
    with pytest.raises(ValueError, match="uninitialized"):
        value(model.null)
    assert all(isinstance(p, NativeParam) for p in model.component_objects(NativeParam))


@pytest.mark.parametrize(
    "source_key",
    [
        "::economics.GDP.alpha",
        "regional::economics.init_capital_factor",
        "timeandregional::population",
    ],
)
def test_sourced_initialization_preserves_documentation_key(source_key):
    model = ConcreteModel()
    model.coefficient = Param(initialize=SourcedValue(3.0, source_key))

    assert value(model.coefficient) == 3.0
    assert model.coefficient.doc == source_key
    assert isinstance(model.coefficient, NativeParam)
    assert PyomoParam is NativeParam


def test_sourced_regional_and_time_data_work_with_filters_and_simulation():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.regions = Set(initialize=["A", "B"], ordered=True)
    model.year = lambda t: 2025 + 5 * t
    model.regional = Param(
        model.regions,
        initialize=SourcedValue({"A": 2.0}, "regional::example.factor"),
        default=4.0,
    )
    data = {(0, "A"): 1.0, (0, "B"): 2.0, (1, "A"): 3.0, (1, "B"): 4.0}
    model.population = Param(
        model.t,
        model.regions,
        initialize=SourcedValue(data, "timeandregional::population"),
    )
    model.output = Var(model.t, model.regions, initialize=0)

    assert [p.name for p in model.component_objects(PyomoParam)] == [
        "regional", "population"
    ]
    assert [p.name for p in get_all_time_dependent_params(model)] == ["population"]
    assert model.population.extract_values() == data
    simulation = SimulationObjectModel(model)
    assert simulation.regional.extract_values() == {"A": 2.0, "B": 4.0}
    assert simulation.population.extract_values() == data
    assert simulation.population.indices == ["t", "regions"]
    assert simulation.output.extract_values() == {index: 0.0 for index in data}


def test_sourced_callable_initialization_remains_a_pyomo_rule():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.factor = Param(initialize=3.0)
    model.calculated = Param(
        model.t,
        initialize=SourcedValue(
            lambda m, t: m.factor * (t + 1), "::example.calculated"
        ),
    )

    assert model.calculated.extract_values() == {0: 3.0, 1: 6.0}


def test_sourced_data_remains_deferred_and_overridable_in_abstract_model():
    model = AbstractModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.factor = Param(initialize=SourcedValue(2.0, "::example.factor"))
    model.input = Param(
        model.t,
        initialize=SourcedValue({0: 1.0, 1: 2.0}, "timeandregional::input"),
    )
    model.derived = Param(
        model.t, initialize=lambda m, t: m.factor * m.input[t]
    )

    assert not model.factor.is_constructed()
    assert not model.input.is_constructed()
    instance = model.create_instance(
        {None: {"factor": {None: 4.0}, "input": {0: 5.0, 1: 7.0}}}
    )
    assert instance.derived.extract_values() == {0: 20.0, 1: 28.0}
    assert instance.factor.doc == "::example.factor"
    assert instance.input.doc == "timeandregional::input"
    assert len(list(instance.component_objects(PyomoParam))) == 3


@pytest.mark.parametrize(
    "constructor,sourced", [(Param, False), (NativeParam, False), (Param, True)]
)
def test_units_mutability_and_validation_remain_effective(constructor, sourced):
    model = ConcreteModel()
    model.limit = constructor(
        initialize=SourcedValue(3.0, "::example.limit") if sourced else 3.0,
        units=units.m,
        mutable=True,
        within=NonNegativeReals,
        validate=lambda m, val: val <= 10,
    )
    model.distance = Var(initialize=2.0, units=units.m)
    model.cap = Constraint(expr=model.distance <= model.limit)

    assert str(units.get_units(model.limit)) == "m"
    assert model.limit.mutable
    assert value(model.cap.upper) == 3.0
    model.limit.set_value(5.0)
    assert value(model.cap.upper) == 5.0
    with pytest.raises(ValueError):
        model.limit.set_value(-1.0)
    with pytest.raises(ValueError):
        model.limit.set_value(11.0)


@pytest.mark.parametrize("sourced", [False, True])
def test_invalid_initial_value_is_rejected_by_pyomo(sourced):
    model = ConcreteModel()
    initializer = SourcedValue(-1.0, "::example.nonnegative") if sourced else -1.0

    with pytest.raises(ValueError):
        model.invalid = Param(initialize=initializer, within=NonNegativeReals)


@pytest.mark.parametrize("initial_value", [False, None])
def test_sourced_false_and_none_are_forwarded_without_coercion(initial_value):
    model = ConcreteModel()
    model.optional = Param(
        initialize=SourcedValue(initial_value, "::example.optional"), within=Any
    )

    assert value(model.optional, exception=False) is initial_value
    if initial_value is None:
        with pytest.raises(ValueError, match="uninitialized"):
            value(model.optional)
    else:
        assert model.optional.extract_values() == {None: initial_value}
    assert model.optional.doc == "::example.optional"


@pytest.mark.parametrize("explicit_doc", ["A description", "::example.other", None])
def test_explicit_doc_conflicts_with_sourced_metadata(explicit_doc):
    with pytest.raises(ValueError, match="omit the explicit doc argument"):
        Param(
            initialize=SourcedValue(3.0, "::example.value"), doc=explicit_doc
        )


def test_sourced_value_metadata_is_frozen():
    sourced = SourcedValue({"A": 2.0}, "regional::example.factor")

    with pytest.raises(FrozenInstanceError):
        sourced.documentation_key = "regional::example.other"
