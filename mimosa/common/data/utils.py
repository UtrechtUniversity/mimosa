from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass
class UnitValues:
    xvalues: Iterable
    yvalues: Iterable
    unit: str = None


def extrapolate(input_values, years, extra_years, meta_info, stabilising_years=50):
    """
    To extrapolate: take growth rate 2090-2100, linearly bring it down to growth rate of 0 in 2150
    Unless emissions are going down, then just keep going down at the same rate.
    """

    became_negative = False

    # First get final change rate
    change_rate = (input_values[-1] - input_values[-2]) / (years[-1] - years[-2])
    minmax = np.maximum if change_rate > 0 else np.minimum

    t_prev = years[-1]
    val_prev = input_values[-1]

    new_values = []

    do_not_go_down = False
    try:
        if "emissions" in str(meta_info[0]).lower() and change_rate < 0:
            do_not_go_down = True
    except IndexError:
        pass

    for t in extra_years:
        if change_rate < 0 and do_not_go_down:
            val = val_prev
        else:
            change = minmax(
                0.0, change_rate - change_rate * (t_prev - 2100.0) / stabilising_years
            )
            val = val_prev + change * (t - t_prev)

        # try:
        #     if meta_info[0] == "emissions":
        #         val = val_prev * (
        #             0.98 ** (t - t_prev)
        #         )  # Reduce 2% per year for emissions after 2100
        # except IndexError:
        #     pass
        # if val < 0:
        #     val = 0.1
        #     became_negative = True

        new_values.append(val)

        val_prev = val
        t_prev = t

    if became_negative:
        print("Extrapolation became negative for", meta_info)
    return np.concatenate([input_values, new_values])
