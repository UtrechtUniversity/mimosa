import re
import yaml
import sys, os

import mkdocs_table_reader_plugin

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from mimosa import MIMOSA, load_params
from mimosa.common import Constraint
import mimosa.components

params = load_params()
model = MIMOSA(params)

all_constraints = list(model.abstract_model.component_objects(Constraint))

components = []


def recursive_traverse_components(current_component):
    if "get_constraints" in dir(current_component):
        components.append(current_component.__name__)
        return

    for c in dir(current_component):
        if c.startswith("_"):
            continue

        component = getattr(current_component, c)
        recursive_traverse_components(component)


def define_env(env):
    for constraint in all_constraints:
        env.variables[constraint.name] = constraint.doc

    @env.macro
    def read_csv_macro(*args, **kwargs):
        return mkdocs_table_reader_plugin.readers.read_csv(*args, **kwargs)

    # get mkdocstrings' Python handler
    python_handler = env.conf["plugins"]["mkdocstrings"].get_handler("python")

    # get the `update_env` method of the Python handler
    update_env = python_handler.update_env

    # override the `update_env` method of the Python handler
    def patched_update_env(md, config):
        update_env(md, config)

        # get the `convert_markdown` filter of the env
        convert_markdown = python_handler.env.filters["convert_markdown"]

        # build a chimera made of macros+mkdocstrings
        def render_convert(markdown: str, *args, **kwargs):
            return convert_markdown(env.render(markdown), *args, **kwargs)

        # patch the filter
        python_handler.env.filters["convert_markdown"] = render_convert

    # patch the method
    python_handler.update_env = patched_update_env
