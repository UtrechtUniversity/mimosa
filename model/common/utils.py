##############################################
# Common functions and utilities
# --------------------------------------------
#
#
##############################################
import time

from numpy import pi

from pyomo.environ import Var, Constraint, atan


def scale_to_a(scale):
    return 25.0 / scale


def soft_switch(x, scale=1.0):
    """Approximates 0 for x <= 0 and 1 for x > 0
    Args:
        x
        scale (float, optional): order of magnitude of expected values. Defaults to 1.0.
    """
    a = scale_to_a(scale)
    return atan(a * x) / pi + 0.5


def soft_min(x, scale=1.0):
    """Soft minimum: approximates the function f(x)=x for x > 0 and f(x)=0 for x <= 0
    Args:
        x
        scale (float, optional): order of magnitude of expected values. Defaults to 1.0.
    Returns:
        approximately x if x > 0 and 0 if x <= 0
    """
    a = scale_to_a(scale)
    soft_min_value = soft_switch(x, scale) * x + 1 / (a * pi)
    return soft_min_value

    # Make sure the final answer is positive. Increases computing time, but reduces errors.
    # return sqrt(
    #     soft_min_value ** 2
    # )


def soft_max(x, maxval, scale=1.0):
    return -soft_min(maxval - x, scale) + maxval


def total_at_t(regional_array, t_i=0):
    """Only used for GEKKO"""
    return sum([regional[t_i] for regional in regional_array])


def firstk(dictionary):
    """Returns the first key of a dictionary"""
    keys = list(dictionary.keys())
    return keys[0]


def first(dictionary):
    """Returns the first element (value) of a dictionary"""
    return dictionary[firstk(dictionary)]


def add_constraint(m, constraint):
    """Adds a constraint to the model
    
    It first generates a unique name, then adds
    the constraint using this new name
    """
    n = len([_ for _ in m.component_objects()])
    name = "constraint_{}".format(n)
    m.add_component(name, constraint)


curr_tick_time = None
curr_tick_name = None


def tick(name=None):
    global curr_tick_time, curr_tick_name
    now = time.time()
    if curr_tick_name is not None:
        # TODO set debug logging level
        print("{} took {:.3g} seconds.".format(curr_tick_name, now - curr_tick_time))
    curr_tick_time = now
    curr_tick_name = name


def timer(name):
    """Decorator which times functions

    Arguments:
        name {str} -- Description of the function
    """

    def decorator(fct):
        def wrapper(*args, **kwargs):
            tick(name)
            result = fct(*args, **kwargs)
            tick()
            return result

        return wrapper

    return decorator


class FctToList:
    def __init__(self, fct):
        self.fct = fct

    def __getitem__(self, item):
        if type(item) == tuple:
            return self.fct(*item)
        else:
            return self.fct(item)

    def __call__(self, *item):
        return self.__getitem__(item)
