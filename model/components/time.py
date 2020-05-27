import numpy as np
from model.common.config import params

def create_time(m):
    # Create time variable
    t0 = params['time']['start']
    t1 = params['time']['end']
    dt = params['time']['dt']
    years = np.arange(t0, t1+dt, dt, dtype=float)

    # Time masks for final value and beyond 2100
    _mask_final_np = np.zeros_like(years)
    _mask_final_np[-1] = 1
    mask_final = m.Param(_mask_final_np)

    _mask_after_2100_np = np.zeros_like(years)
    _mask_after_2100_np[years >= 2100] = 1
    mask_after_2100 = m.Param(_mask_after_2100_np)

    masks = {
        'final': mask_final,
        'after_2100': mask_after_2100
    }

    m.time = years - years[0]

    # Time variable to be used in equations
    m.t = m.Var(value=0, name='t')
    m.Equation(m.t.dt() == 1)

    return years, masks