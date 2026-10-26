from mimosa.common import ConcreteModel
from mimosa.common.utils import load_from_registry
from mimosa.core.model_inputs import ModelInputs

from . import (
    noregime,
    equal_mitigation_costs,
    equal_total_costs,
    per_cap_convergence,
    ability_to_pay,
    equal_cumulative_per_cap,
)


EFFORTSHARING_MODULES = {
    "noregime": noregime.get_constraints,
    "equal_mitigation_costs": equal_mitigation_costs.get_constraints,
    "equal_total_costs": equal_total_costs.get_constraints,
    "per_cap_convergence": per_cap_convergence.get_constraints,
    "ability_to_pay": ability_to_pay.get_constraints,
    "equal_cumulative_per_cap": equal_cumulative_per_cap.get_constraints,
}


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    """Build the selected effortsharing module."""

    module = inputs.config_value("model structure.effortsharing module")
    get_module_constraints = load_from_registry(module, EFFORTSHARING_MODULES)
    return get_module_constraints(m, inputs)
