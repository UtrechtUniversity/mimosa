"""
Parsers for YAML config file:

- GeneralParser (*)
    - StringParser
    - FilepathParser
    - BoolParser
    - NumParser (*)
        - FloatParser
        - IntParser
    - EnumParser
    - QuantityParser
    - ListParser
        - DictParser

(*): Abstract class

These parsers are registered in the PARSER_FACTORY with their
associated parser type name (e.g. "str" for StringParser).
"""

import numpy as np
from abc import ABC, abstractmethod, abstractproperty
from pint import (
    DimensionalityError,
    OffsetUnitCalculusError,
    UndefinedUnitError,
    DefinitionSyntaxError,
)
from mimosa.common.units import Quantity
from . import get_nested


class GeneralParser(ABC):
    def __init__(self, node: dict, *args, **kwargs):
        try:
            self.type = node["type"]
        except KeyError:
            raise KeyError(f"Node should contain a type: {node}")

        self.descr = node.get("descr", "")
        self.default = node.get("default", None)
        self.can_be_false = node.get("can_be_false", False)

    def error(self, error_message):
        raise ValueError(
            f"""
            {error_message}
            Type: {self.type}
            Description: {self.descr}
            Default value: {self.default}
            Can be false: {self.can_be_false}
        """
        )

    @abstractmethod
    def parse(self, value):
        pass

    def get(self, user_config: dict, keys: list):
        try:
            to_be_parsed = get_nested(user_config, keys)
        except KeyError:
            # If it is not defined in the user config file, use the default value
            to_be_parsed = self.default
        return self.parse(to_be_parsed)

    def check_false(self, value):
        if self.can_be_false and self.is_falsy(value):
            return True
        return False

    def to_markdown(self, indent):
        return f"""
{indent}{self.descr}

{indent}- Type: {self.type}

{indent}- Default: {self.default}

{indent}- Can be false: {self.can_be_false}

        """

    def to_string(self):
        return f"{self.descr}. Type: {self.type}. Default: {self.default}.{' Can also be false.' if self.can_be_false else ''}"

    def __repr__(self):
        return f"{self.__class__}: ({self.descr}). Default: {self.default}"

    @staticmethod
    def is_truthy(value):
        return value in [1, True, "True", "true", "yes"]

    @staticmethod
    def is_falsy(value):
        return value in [0, False, "False", "false", "no"]


class StringParser(GeneralParser):
    """
    String value
    """

    def parse(self, value):
        if self.check_false(value):
            return False
        return str(value)


class StringOrPlainDictParser(GeneralParser):
    """
    Either a string or a dictionary. The keys/values of the dictionary are not checked or parsed separately.
    """

    def parse(self, value):
        if self.check_false(value):
            return False

        if isinstance(value, dict):
            return value

        return str(value)


class FilepathParser(GeneralParser):
    """
    Filepath value. Currently exactly the same as the string type.
    """

    def parse(self, value):
        if self.check_false(value):
            return False
        # Should check whether file exists here
        return str(value)


class BoolParser(GeneralParser):
    """
    Boolean value (true or false).
    """

    def parse(self, value):
        if self.check_false(value):
            return False

        if self.is_truthy(value):
            parsed_value = True
        elif self.is_falsy(value):
            parsed_value = False
        else:
            self.error(f"Value {value} can not be parsed to a valid boolean")
        return parsed_value


class NumParser(GeneralParser):
    @abstractproperty
    def num_type_fct(self):
        pass

    def __init__(self, node, *args, **kwargs):
        GeneralParser.__init__(self, node, *args, **kwargs)
        self.min = node.get("min", -np.inf)
        self.max = node.get("max", np.inf)

    def parse(self, value):
        if self.check_false(value):
            return False
        try:
            parsed_value = self.num_type_fct(value)
        except ValueError:
            self.error(
                f"Value {value} can not be parsed to a {self.num_type_fct.__name__}"
            )
        # Check if value within bounds
        if parsed_value < self.min or parsed_value > self.max:
            self.error(
                f"Value {parsed_value} not within bounds ({self.min}, {self.max})"
            )
        return parsed_value

    def to_string(self):
        return f"{super().to_string()} Min: {self.min}. Max: {self.max}."

    def to_markdown(self, indent):
        return (
            super().to_markdown(indent)
            + f"\n\n{indent}- Min: {self.min}\n\n{indent}- Max: {self.max}\n\n"
        )


class FloatParser(NumParser):
    """
    Numerical value (float)

    Extra properties:

    * `min`: lower bound of parameter (default: -inf)
    * `max`: upper bound of parameter (default: +inf)
    """

    @property
    def num_type_fct(self):
        return float


class IntParser(NumParser):
    """
    Numerical value (integer)

    Extra properties:

    * `min`: lower bound of parameter (default: -inf)
    * `max`: upper bound of parameter (default: +inf)
    """

    @property
    def num_type_fct(self):
        return int


class EnumParser(GeneralParser):
    """
    Enum (discrete list of options)

    Extra properties:

    * `values`: list of allowed values
    """

    def __init__(self, node, *args, **kwargs):
        GeneralParser.__init__(self, node, *args, **kwargs)
        self.allowed_values = node["values"]
        if self.default not in self.allowed_values:
            self.error(
                f"Default value {self.default} not in allowed values {self.allowed_values}"
            )

    def parse(self, value):
        if self.check_false(value):
            return False
        if value not in self.allowed_values:
            self.error(f"Value {value} not in allowed values {self.allowed_values}")
        return value

    def to_string(self):
        return f"{super().to_string()} Allowed values: {self.allowed_values}."

    def to_markdown(self, indent):
        markdown = f"{super().to_markdown(indent)}\n{indent}- Allowed values:\n"
        for value in self.allowed_values:
            markdown += f"{indent}    - {value}\n"
        return markdown


class QuantityParser(GeneralParser):
    """
    Quantity (value with unit). The provided value will be converted to the `unit`, if possible.

    For example, if the `unit` of a parameter is GtCO2, and the parameter value provided by the user
    is "1000 MtCO2", the value will be converted automatically to "1 GtCO2". The value passed to MIMOSA will
    therefore be 1, and not 1000. If the user provides "1000 US$", MIMOSA will raise an exception, as this
    cannot be converted to GtCO2.

    Extra properties:

    * `unit`: Unit of the quantity
    """

    def __init__(self, node, quant: Quantity, *args, **kwargs):
        GeneralParser.__init__(self, node, *args, **kwargs)
        self.unit = node["unit"]
        self.quant = quant

    def parse(self, value):
        if self.check_false(value):
            return False
        # Try to parse the quantity
        try:
            parsed = self.quant(value, self.unit, can_be_false=False)
        except (
            DimensionalityError,
            DefinitionSyntaxError,
            OffsetUnitCalculusError,
            UndefinedUnitError,
        ):
            self.error(f"Cannot parse quantity `{value}` to unit `{self.unit}`")
        return value  # Returns the string, unit will be really converted when instantiating the model

    def to_string(self):
        return f"{super().to_string()} Unit: {self.unit}."

    def to_markdown(self, indent):
        return super().to_markdown(indent) + f"\n\n{indent}- Unit: {self.unit}"


class ListParser(GeneralParser):
    """
    List of values. The values are also parsed individually, depending on the parser type given in the property `values`.

    Extra properties:

    * `values`: parser information for the values. For example, the values can be int, float, values with units, etc.
    """

    def __init__(self, node, quant, *args, **kwargs):
        GeneralParser.__init__(self, node, quant, *args, **kwargs)
        self.values_parser = (
            PARSER_FACTORY.create_parser(node["values"], quant)
            if "values" in node
            else None
        )

    @staticmethod
    def parse_if_not_none(parser: GeneralParser, value):
        """If the value is None, simply None is returned. Otherwise each value of the list is parsed."""
        return parser.parse(value) if parser is not None else value

    def parse(self, value):
        if self.check_false(value):
            return False
        if isinstance(value, list):
            parsed_list = [
                self.parse_if_not_none(self.values_parser, list_value)
                for list_value in value
            ]
            return parsed_list
        elif value is None:
            return []
        self.error(f"Cannot parse list {value}")


class DictParser(ListParser):
    """
    Dictionary with keys and values. The values are also parsed individually, depending on the parser type given in the property `values`.

    Extra properties:

    * `values`: parser information for the values. For example, the values can be int, float, values with units, etc.
    * `keys`: parser information for the keys
    """

    def __init__(self, node, quant, *args, **kwargs):
        ListParser.__init__(self, node, quant, *args, **kwargs)
        # DictParser has an extra keys-parser compared to ListParser
        self.keys_parser = (
            PARSER_FACTORY.create_parser(node["keys"], quant)
            if "keys" in node
            else None
        )

    def parse(self, value):
        if self.check_false(value):
            return False
        if isinstance(value, dict):
            parsed_dict = {
                self.parse_if_not_none(
                    self.keys_parser, dict_key
                ): self.parse_if_not_none(self.values_parser, dict_value)
                for dict_key, dict_value in value.items()
            }
            return parsed_dict
        elif value is None:
            return {}
        self.error(f"Cannot parse dictionary {value}")


class DatasourceParser(DictParser):
    """
    Data source for a variable. It's a dictionary with the keys `variable`, `unit`, `scenario`, `model`, and `file`.
    """

    def parse(self, value):
        if self.check_false(value):
            return False
        if isinstance(value, dict):
            parsed_dict = DictParser.parse(self, value)
            # Check if the keys `variable`, `unit`, `scenario`, `model`, and `file` are present
            for key in ["variable", "unit", "scenario", "model", "file"]:
                if key not in parsed_dict:
                    self.error(f"Key {key} not found in datasource {value}")

            return parsed_dict
        self.error(f"Cannot parse datasource {value}. Must be a dictionary.")


class ParserFactory:
    def __init__(self):
        self.parsers = {}

    def register_parser(self, typename: str, parser: GeneralParser):
        parser.type = typename
        self.parsers[typename] = parser

    def create_parser(self, node: dict, quant: Quantity) -> GeneralParser:
        typename = node["type"]
        try:
            parser = self.parsers[typename]
        except KeyError:
            raise KeyError("Cannot find parser of type {}".format(typename))
        return parser(node, quant)


PARSER_FACTORY = ParserFactory()
PARSER_FACTORY.register_parser("float", FloatParser)
PARSER_FACTORY.register_parser("int", IntParser)
PARSER_FACTORY.register_parser("bool", BoolParser)
PARSER_FACTORY.register_parser("str", StringParser)
PARSER_FACTORY.register_parser("enum", EnumParser)
PARSER_FACTORY.register_parser("quantity", QuantityParser)
PARSER_FACTORY.register_parser("list", ListParser)
PARSER_FACTORY.register_parser("dict", DictParser)
PARSER_FACTORY.register_parser("datasource", DatasourceParser)
PARSER_FACTORY.register_parser("filepath", FilepathParser)
PARSER_FACTORY.register_parser("str_or_plain_dict", StringOrPlainDictParser)
