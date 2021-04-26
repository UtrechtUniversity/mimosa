"""
Parses the config.yaml file and checks for consistency with the default config template.
"""

import os
import yaml

if __name__ == "__main__":
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))
    from utils import PARSER_FACTORY, set_nested
else:
    from .utils import PARSER_FACTORY, set_nested

from model.common.units import Quantity


def load_yaml(filename):
    full_filename = os.path.join(
        os.path.dirname(__file__), "../../../inputdata/config/", filename
    )
    with open(full_filename, "r", encoding="utf8") as configfile:
        output = yaml.safe_load(configfile)
    return output


def recursive_traverse(curr_keys, subset, joined_dict, quant=None):
    for key, node in subset.items():
        keys = list(curr_keys) + [key]
        if isinstance(node, dict) and "type" not in node:
            recursive_traverse(keys, node, joined_dict, quant)
        else:
            parser = PARSER_FACTORY.create_parser(node, quant)
            set_nested(joined_dict, keys, parser.get(user_yaml, keys))


default_units = load_yaml("default_units.yaml")
default_yaml = load_yaml("config_default.yaml")
user_yaml = load_yaml("config.yaml")

units = {}
recursive_traverse([], default_units, units)
quant = Quantity(units)


params = {"default units": units["default units"]}
recursive_traverse([], default_yaml, params, quant)

