##############################################
# Common functions and utilities
# --------------------------------------------
#
#
##############################################

def total_at_t(regional_array, t_i = 0):
    return sum([regional[t_i] for regional in regional_array])