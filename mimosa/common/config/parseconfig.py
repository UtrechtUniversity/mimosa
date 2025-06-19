"""
Parses the config.yaml file and checks for consistency with the default config template.
"""

import re

from mimosa.common.utils import load_yaml
from mimosa.common import quant

from .utils import PARSER_FACTORY, set_nested, get_nested, flatten


def recursive_traverse(dict_to_traverse, leaf_function, leaf_criterium=None):
    if leaf_criterium is None:
        leaf_criterium = lambda x: not isinstance(x, dict)

    def _do_recursive_traverse(curr_keys, subset):
        for key, node in subset.items():
            keys = list(curr_keys) + [key]
            if leaf_criterium(node):
                leaf_function(keys, node)
            else:
                _do_recursive_traverse(keys, node)

    _do_recursive_traverse([], dict_to_traverse)


def parse_params(default_yaml, user_yaml, return_parser_tree=False):
    parsed_dict = {}
    parser_tree = {}

    def leaf_criterium(node):
        return not isinstance(node, dict) or "type" in node

    def leaf_function(keys, node):
        parser = PARSER_FACTORY.create_parser(node, quant)

        # Save the parser instance for possible later use
        set_nested(parser_tree, keys, parser)

        # Save the parsed value
        set_nested(parsed_dict, keys, parser.get(user_yaml, keys))

    recursive_traverse(default_yaml, leaf_function, leaf_criterium)

    if return_parser_tree:
        return parsed_dict, parser_tree

    return parsed_dict


def create_leaf_criterium(parser_tree):
    def leaf_criterium(keys, node):
        try:
            parser_type = get_nested(parser_tree, keys).type
        except (AttributeError, KeyError):
            parser_type = None
        if isinstance(node, dict) and parser_type not in ["dict", "datasource"]:
            return False
        return True

    return leaf_criterium


def check_obsolete_params(user_yaml, parsed_params, parser_tree):

    leaf_criterium = create_leaf_criterium(parser_tree)

    keys_user = set(flatten(user_yaml, leaf_criterium=leaf_criterium))
    keys_parsed = set(flatten(parsed_params, leaf_criterium=leaf_criterium))

    # Check keys which are in user config, but not in parsed file
    # These are obsolete/unused/misspelled parameters
    num_obsolete = 0
    obsolete_params = []
    for key in set(keys_user) - set(keys_parsed):
        num_obsolete += 1
        obsolete_params.append(key)
    if num_obsolete > 0:
        raise RuntimeWarning(
            "Some config parameters are obsolete or misspelled:\n"
            + "\n".join(obsolete_params)
        )


def load_default_yaml():
    return load_yaml("config_default.yaml")


def check_params(input_params, return_parser_tree=False):
    default_yaml = load_default_yaml()

    parsed_params, params_parser_tree = parse_params(
        default_yaml, input_params, return_parser_tree=True
    )

    check_obsolete_params(input_params, parsed_params, params_parser_tree)

    if return_parser_tree:
        return parsed_params, params_parser_tree
    return parsed_params


def parse_param_values(params):
    """
    Check parameter values for references to other parameter values

    References to other parameter values can be made like:

    "{SSP}"

    or

    "{emissions - carbonbudget}" (join the nested keys with " - ")

    """

    # Perform a recursive traversal of the parameter dictionary and parse
    # all values that contain references to other parameters

    def leaf_criterium(node):
        return not isinstance(node, dict)

    def leaf_function(keys, node):
        if not isinstance(node, str):
            return
        for match in re.findall(r"\{([\w -]+)\}", node):
            try:
                other_value = get_nested(params, match.split(" - "))
                new_value = node.replace(f"{{{match}}}", other_value)
                set_nested(params, keys, new_value)
            except KeyError:
                pass

    recursive_traverse(params, leaf_function, leaf_criterium)

    return params


def load_params(user_yaml_filename=None):
    if user_yaml_filename is None:
        user_yaml = {}
    else:
        user_yaml = load_yaml(user_yaml_filename)
    return check_params(user_yaml)
