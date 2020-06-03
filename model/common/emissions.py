import numpy as np
from model.common.config import params
from model.common import data



def max_emissions(baseline_emissions):
    emissions_np = np.array([var.value for var in baseline_emissions])
    return np.sum(emissions_np, axis=0).max()