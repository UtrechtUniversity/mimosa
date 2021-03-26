"""
Common functions and utilities
"""

import time


def firstk(dictionary):
    """Returns the first key of a dictionary"""
    keys = list(dictionary.keys())
    return keys[0]


def first(dictionary):
    """Returns the first element (value) of a dictionary"""
    return dictionary[firstk(dictionary)]


def timer(name):
    """Decorator which times functions

    Arguments:
        name {str} -- Description of the function
    """

    def decorator(fct):
        def wrapper(*args, **kwargs):
            time1 = time.time()
            result = fct(*args, **kwargs)
            time2 = time.time()
            print("{} took {:.3g} seconds.".format(name, time2 - time1))
            return result

        return wrapper

    return decorator
