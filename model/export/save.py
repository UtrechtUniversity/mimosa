import pandas as pd
import json
import os
import random
from pyomo.environ import value
import hashlib

from model.common import utils

def save_output(params, m, experiment=None, random_id=False, folder='output'):

    # 1. Create a unique identifier
    if random_id:
        id = '{:08x}'.format(random.getrandbits(32))
    else:
        id = hashlib.md5(json.dumps(params).encode()).hexdigest()[:9]

    # 2. Save the data
    global_vars = [
        m.global_emissions,
        m.temperature,
        m.cumulative_emissions,
        m.learning_factor
    ]
    regional_vars = [
        [m.baseline, 'baseline'],
        [m.population, 'population'],
        m.regional_emissions,
        m.carbonprice,
        m.capital_stock,
        m.GDP_gross, m.GDP_net,
        m.abatement_costs,
        m.damage_costs,
        m.resid_damages,
        m.gross_damages,
        m.adapt_costs,
        m.adapt_level,
        m.consumption,
        m.utility
    ]
    try:
        global_vars.extend([
            m.temperaturedot,
            m.smoothed_factor
        ])
    except:
        pass
    rows = []
    for var in global_vars:
        var_to_row(rows, m, var, False)
    for var in regional_vars:
        var_to_row(rows, m, var, True)
    df = rows_to_dataframe(rows, m)

    add_param_columns(df, params, id, experiment)


    # 3. Save the CSV file
    os.makedirs(folder+'/', exist_ok=True)
    filename = f'{id}' if experiment is None else f'{experiment}_{id}'

    df.to_csv(f'{folder}/output_{filename}.csv', float_format='%.6g', index=False)

    # 3. Save the param file
    os.makedirs(f'{folder}/params/', exist_ok=True)
    with open (f'{folder}/params/params_{filename}.json', 'w') as fp:
        json.dump({id: params}, fp)



    return

def var_to_row(rows, m, var, is_regional):
    # If var is a list, second element is the name
    if type(var) is list:
        name = var[1]
        var = var[0]
    else:
        name = var.name
    
    # Check if var is a function or a pyomo variable
    fct = var if callable(var) else (
        (lambda t,r: value(var[t,r])) if is_regional else \
        (lambda t:   value(var[t]))
    )

    if is_regional:
        for r in m.regions:
            rows.append([name, r]+[fct(t,r) for t in m.t])
    else:
        rows.append([name, 'Global']+[fct(t) for t in m.t])

    
def rows_to_dataframe(rows, m):
    years = ['{:g}'.format(value(m.beginyear)+t) for t in m.t]
    columns = ['Variable', 'Region'] + years
    df = pd.DataFrame(rows, columns=columns)
    return df


def add_param_columns(df, params, id, experiment):
    values = {
        'carbonbudget': params['emissions']['carbonbudget'],
        'minlevel': params['emissions']['min level'],
        'inertia': params['emissions']['inertia']['regional'],
        'gamma': params['economics']['MAC']['gamma'],
        'PRTP': params['economics']['PRTP'],
        'damage_coeff': utils.first(params['regions'])['damages']['a2'], # NOTE, only for global run
        'perc_reversible': params['economics']['damages']['percentage reversible'],
        'TCRE': params['temperature']['TCRE']
    }
    for i, (name, value) in enumerate(values.items()):
        df.insert(i+2, name, value)

    # Add ID:
    df.insert(0, 'ID', id)
    if experiment is not None:
        df.insert(1, 'Experiment', experiment)