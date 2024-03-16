"""
Parses the config.yaml file and checks for consistency with the default config template.
"""

from mimosa.common.utils import load_yaml
from mimosa.common import quant

from .utils import PARSER_FACTORY, set_nested, get_nested, flatten


def parse_params(default_yaml, user_yaml, return_parser_tree=False):
    parsed_dict = {}
    parser_tree = {}

    def _recursive_traverse(curr_keys, subset):
        for key, node in subset.items():
            keys = list(curr_keys) + [key]
            if isinstance(node, dict) and "type" not in node:
                _recursive_traverse(keys, node)
            else:
                parser = PARSER_FACTORY.create_parser(node, quant)

                # Save the parser instance for possible later use
                set_nested(parser_tree, keys, parser)

                # Save the parsed value
                set_nested(parsed_dict, keys, parser.get(user_yaml, keys))

    _recursive_traverse([], default_yaml)

    if return_parser_tree:
        return parsed_dict, parser_tree

    return parsed_dict


def check_obsolete_params(user_yaml, parsed_params, parser_tree):
    def leaf_criterium(keys, node):
        try:
            parser_type = get_nested(parser_tree, keys).type
        except (AttributeError, KeyError):
            parser_type = None
        if isinstance(node, dict) and parser_type != "dict":
            return False
        return True

    keys_user = set(flatten(user_yaml, leaf_criterium=leaf_criterium))
    keys_parsed = set(flatten(parsed_params, leaf_criterium=leaf_criterium))

    # Check keys which are in user config, but not in parsed file
    # These are obsolete/unused/misspelled parameters
    num_obsolete = 0
    for key in set(keys_user) - set(keys_parsed):
        num_obsolete += 1
        print(f"Obsolete key: {key}")
    if num_obsolete > 0:
        raise RuntimeWarning("Some config parameters are obsolete.")


def check_params(input_params, return_parser_tree=False):
    default_yaml = load_yaml("config_default.yaml")

    parsed_params, params_parser_tree = parse_params(
        default_yaml, input_params, return_parser_tree=True
    )

    check_obsolete_params(input_params, parsed_params, params_parser_tree)

    if return_parser_tree:
        return parsed_params, params_parser_tree
    return parsed_params


def load_params(user_yaml_filename=None):
    if user_yaml_filename is None:
        user_yaml = {}
    else:
        user_yaml = load_yaml(user_yaml_filename)
    return check_params(user_yaml)
