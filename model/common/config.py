"""
Reads the config file in YAML format and makes a dictionary out of it
"""
import os
import yaml

CONFIG_FILENAME = "config.yaml"


def read_params(config_filename=CONFIG_FILENAME):
    full_filename = os.path.join(
        os.path.dirname(__file__), "../../inputdata/config", config_filename,
    )

    with open(full_filename, "r", encoding="utf8") as configfile:
        params = yaml.safe_load(configfile)

    return params


params = read_params()
