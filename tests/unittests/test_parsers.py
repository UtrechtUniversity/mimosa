import pytest

from mimosa.common.config.utils import PARSER_FACTORY
from mimosa.common import quant


def test_float_parser():
    p = PARSER_FACTORY.create_parser({"type": "float"}, quant)
    assert p.parse(1.5) == 1.5

    # Test if raises error when given a string
    with pytest.raises(ValueError):
        p.parse("test")

    p2 = PARSER_FACTORY.create_parser({"type": "float", "min": 5.5, "max": 10}, quant)
    assert p2.parse(5.5) == 5.5
    assert p2.parse(10) == 10

    with pytest.raises(ValueError):
        p2.parse(4)

    with pytest.raises(ValueError):
        p2.parse(11.1)

    p3 = PARSER_FACTORY.create_parser({"type": "float", "can_be_false": True}, quant)
    assert p3.parse(False) is False


def test_int_parser():
    p = PARSER_FACTORY.create_parser({"type": "int"}, quant)
    assert p.parse(1) == 1
    assert p.parse(1.3) == 1

    # Test if raises error when given a string
    with pytest.raises(ValueError):
        p.parse("test")

    p2 = PARSER_FACTORY.create_parser({"type": "int", "min": 5, "max": 10}, quant)
    assert p2.parse(5) == 5
    assert p2.parse(10) == 10

    with pytest.raises(ValueError):
        p2.parse(4)

    with pytest.raises(ValueError):
        p2.parse(11)

    p3 = PARSER_FACTORY.create_parser({"type": "int", "can_be_false": True}, quant)
    assert p3.parse(False) is False


def test_bool_parser():
    p = PARSER_FACTORY.create_parser({"type": "bool"}, quant)
    assert p.parse(True) is True
    assert p.parse(False) is False
    assert p.parse("true") is True
    assert p.parse("false") is False
    assert p.parse("yes") is True
    assert p.parse("no") is False
    assert p.parse(0) is False
    assert p.parse(1) is True

    # Test if raises error when given a string
    with pytest.raises(ValueError):
        p.parse("test")
    with pytest.raises(ValueError):
        p.parse(2)


def test_str_parser():
    p = PARSER_FACTORY.create_parser({"type": "str"}, quant)
    assert p.parse("test") == "test"
    assert p.parse(1) == "1"
    assert p.parse(1.5) == "1.5"
    assert p.parse(True) == "True"

    p2 = PARSER_FACTORY.create_parser({"type": "str", "can_be_false": True}, quant)
    assert p2.parse(False) is False


def test_enum_parser():
    p = PARSER_FACTORY.create_parser(
        {"type": "enum", "values": ["a", "b", "c"], "default": "a"}, quant
    )
    assert p.parse("a") == "a"
    assert p.parse("b") == "b"
    assert p.parse("c") == "c"

    with pytest.raises(ValueError):
        p.parse("d")

    p2 = PARSER_FACTORY.create_parser(
        {
            "type": "enum",
            "values": ["a", "b", "c"],
            "default": "a",
            "can_be_false": True,
        },
        quant,
    )
    assert p2.parse(False) is False

    # Test if raises error if default not in allowed values:
    with pytest.raises(ValueError):
        PARSER_FACTORY.create_parser({"type": "enum", "values": ["a", "b", "c"]}, quant)
    with pytest.raises(ValueError):
        PARSER_FACTORY.create_parser(
            {"type": "enum", "values": ["a", "b", "c"], "default": "d"}, quant
        )

    # Should raise an error if values is not a list
    with pytest.raises(TypeError):
        PARSER_FACTORY.create_parser({"type": "enum", "values": 3}, quant)


def test_quantity_parser():
    p = PARSER_FACTORY.create_parser({"type": "quantity", "unit": "m"}, quant)
    # Parser should only check if value is parsable by quant, and return the string
    assert p.parse("300 m") == "300 m"
    assert p.parse("0.3 km") == "0.3 km"

    # Error if incompatible unit:
    with pytest.raises(ValueError):
        p.parse("5 kg")

    # Error if no unit:
    with pytest.raises(ValueError):
        p.parse("5")
    with pytest.raises(ValueError):
        p.parse(False)

    # Test can_be_false:
    p2 = PARSER_FACTORY.create_parser(
        {"type": "quantity", "unit": "m", "can_be_false": True}, quant
    )
    assert p2.parse(False) is False

    # If unit is empty:
    p3 = PARSER_FACTORY.create_parser({"type": "quantity", "unit": ""}, quant)
    assert p3.parse("5") == "5"

    with pytest.raises(ValueError):
        p3.parse("5 m")


def test_list_parser_without_element_type():
    p = PARSER_FACTORY.create_parser({"type": "list"}, quant)
    assert p.parse([1, 2, 3]) == [1, 2, 3]
    assert p.parse([]) == []

    with pytest.raises(ValueError):
        p.parse("")

    with pytest.raises(ValueError):
        p.parse(False)

    p2 = PARSER_FACTORY.create_parser({"type": "list", "can_be_false": True}, quant)
    assert p2.parse(False) is False


def test_list_parser_with_element_type():
    p = PARSER_FACTORY.create_parser(
        {"type": "list", "values": {"type": "float"}}, quant
    )
    assert p.parse([1, 2.5, 3]) == [1.0, 2.5, 3.0]
    assert p.parse([]) == []

    with pytest.raises(ValueError):
        p.parse(["test"])
    with pytest.raises(ValueError):
        p.parse([1.3, "test"])


def test_list_parser_with_list_of_lists():
    p = PARSER_FACTORY.create_parser(
        {"type": "list", "values": {"type": "list", "values": {"type": "float"}}}, quant
    )
    assert p.parse([[1, 2.5], [3, 4.5]]) == [[1.0, 2.5], [3.0, 4.5]]
    assert p.parse([[1, 2, 3], [10.5, 11.5]]) == [[1.0, 2.0, 3.0], [10.5, 11.5]]

    with pytest.raises(ValueError):
        p.parse([["test"]])
    with pytest.raises(ValueError):
        p.parse([[1.3, "test"]])
    with pytest.raises(ValueError):
        p.parse([1.3, "test"])


def test_dict_parser():
    p = PARSER_FACTORY.create_parser({"type": "dict"}, quant)
    assert p.parse({"a": 1, 3: 2}) == {"a": 1, 3: 2}
    assert p.parse({}) == {}

    with pytest.raises(ValueError):
        p.parse("")

    with pytest.raises(ValueError):
        p.parse([1, 2, 3])


def test_dict_parser_value_type():
    p = PARSER_FACTORY.create_parser(
        {"type": "dict", "values": {"type": "float"}}, quant
    )
    assert p.parse({"a": 1, 3: 2.5}) == {"a": 1.0, 3: 2.5}

    with pytest.raises(ValueError):
        p.parse({"a": "test", 3: 2.5})


def test_dict_parser_key_type():
    p = PARSER_FACTORY.create_parser({"type": "dict", "keys": {"type": "str"}}, quant)
    assert p.parse({"a": 1, "b": 2.5}) == {"a": 1, "b": 2.5}
    assert p.parse({1: 1, "3": 2.5}) == {"1": 1, "3": 2.5}


def test_dict_parser_key_value_type():
    p = PARSER_FACTORY.create_parser(
        {
            "type": "dict",
            "keys": {"type": "str"},
            "values": {"type": "list", "values": {"type": "float"}},
        },
        quant,
    )
    assert p.parse({"a": [1, 2], "b": [2.5, 5]}) == {"a": [1.0, 2.0], "b": [2.5, 5.0]}
    assert p.parse({1: [1, 2], "3": [2.5, 5]}) == {"1": [1.0, 2.0], "3": [2.5, 5.0]}

    with pytest.raises(ValueError):
        p.parse({1: 1, 3: 2.5})

    with pytest.raises(ValueError):
        p.parse({"a": "test", "b": 2.5})
    with pytest.raises(ValueError):
        p.parse({"a": [1, 2], 3: [2.5, "test"]})


def _create_datasource_dict():
    return {
        "variable": "GDP|PPP",
        "unit": "USD",
        "scenario": "scenario1",
        "model": "model1",
        "file": "file1.csv",
    }


def test_datasource_parser():
    p = PARSER_FACTORY.create_parser({"type": "datasource"}, quant)
    value = _create_datasource_dict()
    assert p.parse(value) == value


@pytest.mark.parametrize("key", ["variable", "unit", "scenario", "model", "file"])
def test_datasource_missing_info(key):
    p = PARSER_FACTORY.create_parser({"type": "datasource"}, quant)
    value = _create_datasource_dict()
    del value[key]
    with pytest.raises(ValueError):
        p.parse(value)


def test_stringorplaindict_parser():
    p = PARSER_FACTORY.create_parser({"type": "str_or_plain_dict"}, quant)
    assert p.parse("test") == "test"
    assert p.parse({"a": 1}) == {"a": 1}
    assert p.parse(1) == "1"

    assert p.parse(False) == "False"

    p2 = PARSER_FACTORY.create_parser(
        {"type": "str_or_plain_dict", "can_be_false": True}, quant
    )
    assert p2.parse(False) is False
