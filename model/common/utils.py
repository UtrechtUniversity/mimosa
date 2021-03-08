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


def add_constraint(m, constraint, name=None):
    """Adds a constraint to the model

    It first generates a unique name, then adds
    the constraint using this new name
    """
    n = len([_ for _ in m.component_objects()])
    name = (
        "constraint_{}".format(n)
        if name is None
        else "constraint_{}_{}".format(name, n)
    )
    m.add_component(name, constraint)
    return name


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
