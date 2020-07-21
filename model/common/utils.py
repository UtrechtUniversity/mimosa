##############################################
# Common functions and utilities
# --------------------------------------------
#
#
##############################################
import time

def total_at_t(regional_array, t_i = 0):
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
    name = 'constraint_{}'.format(n)
    m.add_component(name, constraint)

curr_tick_time = None
curr_tick_name = None
def tick(name=None):
    global curr_tick_time, curr_tick_name
    now = time.time()
    if curr_tick_name is not None:
        # TODO set debug logging level
        print('{} took {:.3g} seconds.'.format(curr_tick_name, now-curr_tick_time))
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