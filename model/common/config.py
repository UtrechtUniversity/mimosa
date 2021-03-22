"""
Reads the config file in YAML format and makes a dictionary out of it
"""
import os
import yaml

config_filename = "config.yaml"
full_filename = os.path.join(
    os.path.dirname(__file__), "../../inputdata/config", config_filename,
)

with open(full_filename, "r", encoding="utf8") as configfile:
    params = yaml.safe_load(configfile)
