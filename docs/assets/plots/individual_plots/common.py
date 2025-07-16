import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
)


import mimosa
from mimosa import MIMOSA
from mimosa.common.config.parseconfig import check_params


params, parser_tree = check_params({}, return_parser_tree=True)


# Create an instance of the MIMOSA model to get the names of each parameter to be parsed
model = MIMOSA(params)
param_store = model.preprocessor._regional_param_store

COLORS = [
    "#5492cd",
    "#ffa900",
    "#003466",
    "#EF550F",
    "#990002",
    "#c47900",
    "#00aad0",
    "#76797b",
]
