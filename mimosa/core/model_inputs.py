"""Explicit input lookup for model-component construction."""

from typing import Any, Callable

import numpy as np

from mimosa.common.config.utils import get_nested
from mimosa.common.data import DataStore
from mimosa.common.parameters import SourcedValue
from mimosa.common.regional_params import RegionalParamStore
from mimosa.common.timegrid import create_time_grid
from mimosa.common.units import quant


class ModelInputs:
    """Look up inputs using a prepared configuration and its existing data stores.

    ``params`` must already be validated, with configuration references resolved.
    The parser tree and both stores must correspond to that configuration. This
    class does not reparse configuration, load files or mutate the supplied inputs.
    Finalise configuration before constructing it: its grid and stores are not
    rebuilt if the configuration subsequently changes.

    Sourced lookups return values with the metadata consumed by MIMOSA's Param
    factory. ``config_value`` returns plain values for construction-time choices.
    """

    year: Callable[[int], float]

    def __init__(
        self,
        params: dict,
        parser_tree: dict,
        data_store: DataStore,
        regional_store: RegionalParamStore,
    ):
        self.params = params
        self.parser_tree = parser_tree
        self.data_store = data_store
        self.regional_store = regional_store
        self.time_grid = create_time_grid(params["time"])
        self.t = range(len(self.time_grid.years))
        self.regions = tuple(params["regions"])

        # Match the existing year callable while capturing only the small year
        # array, rather than retaining/copying data stores through a model's year.
        years = np.asarray(self.time_grid.years)
        self.year = lambda t: years[t]

        pulse_year = self.config_value("emissions.pulse.year")
        pulse_amount = self.config_value("emissions.pulse.amount")
        if pulse_amount != 0 and pulse_year not in self.time_grid.years:
            raise ValueError(
                f"Emissions pulse year {pulse_year} is not on the model time grid."
            )

    def config_value(self, path: str) -> Any:
        """Return a config value, converting scalar quantities to model units.

        Sections and dictionary-valued settings retain their parsed contents;
        quantities within a returned section are not recursively converted.
        """
        keys = path.split(".")
        try:
            result = get_nested(self.params, keys)
        except (KeyError, TypeError) as exc:
            raise KeyError(f"Configuration path {path!r} was not found.") from exc

        try:
            parser = get_nested(self.parser_tree, keys)
        except (KeyError, TypeError):
            # Values inside dictionary-valued settings have no separate parser
            # node (e.g. per-region manual inputs).
            parser = None
        if getattr(parser, "type", None) == "quantity":
            result = quant(result, parser.unit)
        return result

    def config(self, path: str) -> SourcedValue:
        """Return a config value with its ``::config.path`` source key."""
        return SourcedValue(self.config_value(path), f"::{path}")

    def regional(self, category: str, name: str) -> SourcedValue:
        """Return regional data, including configured per-region overrides."""
        try:
            values = self.regional_store.get(category, name)
        except KeyError as exc:
            raise KeyError(
                f"Regional input {category + '.' + name!r} was not found."
            ) from exc
        return SourcedValue(values, f"regional::{category}.{name}")

    def time_regional(self, name: str) -> SourcedValue:
        """Interpolate a baseline input on the configured time/region indices."""
        try:
            values = {
                (t, r): self.data_store.interp_data(self.year(t), r, name)
                for t in self.t
                for r in self.regions
            }
        except KeyError as exc:
            raise KeyError(f"Time-and-region input {name!r} was not found.") from exc
        return SourcedValue(values, f"timeandregional::{name}")

    def mac_ssp_calibration_factor(self) -> SourcedValue:
        """Interpolate MAC calibration keyframes for the selected SSP."""
        source = self.config(
            f"economics.MAC.SSP_calibration_factor.{self.config_value('SSP')}"
        )
        values = {
            t: self.data_store.interp_data_from_dict(self.year(t), source.values)
            for t in self.t
        }
        return SourcedValue(values, source.documentation_key)
