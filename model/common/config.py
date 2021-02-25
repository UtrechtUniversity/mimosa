"""
Reads the config file in YAML format and makes a dictionary out of it
"""
import yaml

config_filename = "input/config.yaml"

with open(config_filename, "r", encoding="utf8") as configfile:
    params = yaml.safe_load(configfile)
