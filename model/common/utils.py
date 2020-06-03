##############################################
# Common functions and utilities
# --------------------------------------------
#
#
##############################################

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