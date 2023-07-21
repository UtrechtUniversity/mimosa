"""
Certain constraints can be deactivated. These are defined in:
    params["simulation"]["disabled_constraints"] = ['carbon_budget', ...]
"""


def deactivate_constraints(m, params):
    if params["simulation"]["deactivated_constraints"] is not None:
        for constraint_name in params["simulation"]["deactivated_constraints"]:
            constraint = getattr(m, f"constraint_{constraint_name}")
            if constraint is not None:
                constraint.deactivate()
