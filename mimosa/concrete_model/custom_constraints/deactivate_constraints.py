"""
Certain constraints can be deactivated. These are defined in:
    params["custom_constraints"]["disabled_constraints"] = ['carbon_budget', ...]
"""


def deactivate_constraints(m, params):
    if params["custom_constraints"]["disabled_constraints"] is not None:
        for constraint_name in params["custom_constraints"]["disabled_constraints"]:
            constraint = getattr(m, f"constraint_{constraint_name}")
            if constraint is not None:
                constraint.deactivate()
