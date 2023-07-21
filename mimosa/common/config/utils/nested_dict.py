def get_nested(dictionary, keys, create=False):
    for key in keys:
        if key not in dictionary and create:
            dictionary[key] = {}
        dictionary = dictionary[key]
    return dictionary


def set_nested(dictionary, keys, value):
    dictionary = get_nested(dictionary, keys[:-1], True)
    dictionary[keys[-1]] = value


def flatten(joined_dict, leaf_criterium=None):

    flattened_dict = {}

    leaf_criterium_default = lambda keys, node: not isinstance(node, dict)

    if leaf_criterium is None:
        leaf_criterium = leaf_criterium_default

    def _recursive_traverse(curr_keys, subset):
        for key, node in subset.items():
            keys = list(curr_keys) + [key]
            if leaf_criterium(keys, node):
                flattened_dict[" - ".join(keys)] = node
            else:
                _recursive_traverse(keys, node)

    _recursive_traverse([], joined_dict)

    return flattened_dict
