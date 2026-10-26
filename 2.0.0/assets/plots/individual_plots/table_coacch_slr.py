import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from .common import mimosa, model, COLORS, param_store


def create_table():

    ##############
    # COACCH SLR param
    ##############

    form_slr_ad = param_store.get("COACCH", "SLR-Ad_form")
    form_slr_noad = param_store.get("COACCH", "SLR-NoAd_form")
    form_slr = pd.DataFrame(
        {
            "SLR (with opt. adapt.)": strip_prefix_form(form_slr_ad),
            "SLR (no adaptation)": strip_prefix_form(form_slr_noad),
        }
    ).rename_axis("Region", axis=0)

    return form_slr


def strip_prefix_form(form_dict):
    return {
        key: value.replace("Robust-", "").replace("OLS-", "")
        for key, value in form_dict.items()
    }
