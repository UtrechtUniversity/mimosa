import pandas as pd
import json
import random
from pyomo.environ import value
import hashlib

def save_output(params, m, random_id=False):

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
        m.regional_emissions,
        m.carbonprice,
        m.capital_stock,
        m.GDP_gross, m.GDP_net,
        m.abatement_costs,
        m.damage_costs,
        m.consumption,
        m.utility
    ]
    rows = []
    for var in global_vars:
        var_to_row(rows, m, var, False)
    for var in regional_vars:
        var_to_row(rows, m, var, True)
    df = rows_to_dataframe(rows, m)

    add_param_columns(df, params, id)

    df.to_csv(f'output/output_{id}.csv', float_format='%.6g')

    # 3. Save the param file
    with open (f'output/params_{id}.json', 'w') as fp:
        json.dump({id: params}, fp)



    return

def var_to_row(rows, m, var, is_regional):
    name = var.name
    if is_regional:
        for r in m.regions:
            rows.append([name, r]+[value(var[t,r]) for t in m.t])
    else:
        rows.append([name, 'Global']+[value(var[t]) for t in m.t])

    
def rows_to_dataframe(rows, m):
    years = ['{:g}'.format(value(m.beginyear)+t) for t in m.t]
    columns = ['Variable', 'Region'] + years
    df = pd.DataFrame(rows, columns=columns)
    return df


def add_param_columns(df, params, id):
    values = {
        'carbonbudget': params['emissions']['carbonbudget'],
        'minlevel': params['emissions']['min level'],
        'inertia': params['emissions']['inertia']['regional'],
        'gamma': params['economics']['MAC']['gamma'],
        'PRTP': params['economics']['PRTP'],
        'damage_coeff': params['economics']['damages']['coeff'],
        'TCRE': params['temperature']['TCRE']
    }
    for i, (name, value) in enumerate(values.items()):
        df.insert(i+2, name, value)

    # Add ID:
    df.insert(0, 'ID', id)