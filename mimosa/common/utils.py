"""
Common functions and utilities
"""

import os
import time
import yaml
from mimosa.common import logger


def firstk(dictionary):
    """Returns the first key of a dictionary"""
    keys = list(dictionary.keys())
    return keys[0]


def first(dictionary):
    """Returns the first element (value) of a dictionary"""
    return dictionary[firstk(dictionary)]


def timer(name, log=False):
    """Decorator which times functions

    Arguments:
        name {str} -- Description of the function
    """

    def decorator(fct):
        def wrapper(*args, **kwargs):
            time1 = time.time()
            result = fct(*args, **kwargs)
            time2 = time.time()
            message = "{} took {:.3g} seconds.".format(name, time2 - time1)
            if log:
                logger.info(message)
            print(message)
            return result

        return wrapper

    return decorator


def load_yaml(filename):
    full_filename = os.path.join(
        os.path.dirname(__file__), "../inputdata/config/", filename
    )
    with open(full_filename, "r", encoding="utf8") as configfile:
        output = yaml.safe_load(configfile)
    return output


class MimosaSolverWarning(Warning):
    pass
