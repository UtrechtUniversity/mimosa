def get_nested(dictionary, keys, create=False):
    for key in keys:
        if key not in dictionary and create:
            dictionary[key] = {}
        dictionary = dictionary[key]
    return dictionary


def set_nested(dictionary, keys, value):
    dictionary = get_nested(dictionary, keys[:-1], True)
    dictionary[keys[-1]] = value
