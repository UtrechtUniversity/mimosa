import yaml

config_filename = 'input/config.yaml'

with open(config_filename, 'r') as configfile:
    params = yaml.safe_load(configfile)