import pytest

from mimosa.common.config.parseconfig import get_nested, set_nested, flatten


@pytest.fixture
def d():
    return {
        "a": {
            "b": {
                "c1": 1,
                "c2": 5,
                "c3": {
                    "d1": "value1",
                    "d2": "value2",
                },
            }
        }
    }


def test_get_nested(d):
    assert get_nested(d, ["a", "b", "c1"]) == 1
    assert get_nested(d, ["a", "b", "c2"]) == 5

    # Test if `create` option works
    assert get_nested(d, ["a", "b", "d"], create=True) == {}
    assert get_nested(d, ["a", "b", "d"]) == {}

    assert get_nested(d, ["a", "e", "f"], create=True) == {}
    assert get_nested(d, ["a", "e", "f"]) == {}

    # Test if `create` option works with False
    with pytest.raises(KeyError):
        get_nested(d, ["a", "b", "g"])


def test_set_nested(d):

    assert d["a"]["b"]["c1"] == 1
    set_nested(d, ["a", "b", "c1"], 10)
    assert d["a"]["b"]["c1"] == 10

    set_nested(d, ["a", "b", "c3"], 20)
    assert d["a"]["b"]["c3"] == 20

    set_nested(d, ["a", "e", "f"], 30)
    assert d["a"]["e"]["f"] == 30


def test_flatten(d):

    assert flatten(d) == {
        "a - b - c1": 1,
        "a - b - c2": 5,
        "a - b - c3 - d1": "value1",
        "a - b - c3 - d2": "value2",
    }

    # Test the leaf_criterium:
    # In this case, check if the keys exist in some other dictionary
    # If they exist, and if the value is "dict", it should also be
    # a leaf.

    d_types_flattened = {
        ("a", "b", "c1"): "int",
        ("a", "b", "c2"): "int",
        ("a", "b", "c3"): "dict",
    }
    assert flatten(
        d,
        leaf_criterium=lambda keys, node: (
            not isinstance(node, dict)
            or d_types_flattened.get(tuple(keys), None) == "dict"
        ),
    ) == {
        "a - b - c1": 1,
        "a - b - c2": 5,
        "a - b - c3": {"d1": "value1", "d2": "value2"},
    }
