"""Construction and configuration mechanics for model components."""

from collections import Counter
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional

from mimosa.common.utils import load_from_registry

from .model_inputs import ModelInputs


@dataclass(frozen=True)
class ComponentDefinition:
    """Connect one model part to its configuration and construction function."""

    name: str
    get_constraints: Optional[Callable] = None
    modules: Optional[Dict[str, Callable]] = None

    def __post_init__(self):
        if (self.get_constraints is None) == (self.modules is None):
            raise ValueError(
                "A component must define either get_constraints or selectable modules"
            )

    def build(self, model, inputs: ModelInputs):
        """Add this component's model objects and return its constraints."""
        get_constraints = self.get_constraints
        if self.modules is not None:
            module = inputs.config_value(f"model structure.{self.name} module")
            get_constraints = load_from_registry(module, self.modules)

        return get_constraints(model, inputs)


def fixed_component(name: str, get_constraints: Callable) -> ComponentDefinition:
    """Define a component that is always included."""
    return ComponentDefinition(name=name, get_constraints=get_constraints)


def selectable_component(
    name: str, modules: Dict[str, Callable]
) -> ComponentDefinition:
    """Define a component selected through ``<name> module`` in the config."""
    return ComponentDefinition(name=name, modules=modules)


def validate_unique_component_names(
    components: Iterable[ComponentDefinition],
) -> None:
    """Reject component catalogues containing the same name more than once."""
    name_counts = Counter(component.name for component in components)
    duplicate_names = sorted(
        name for name, count in name_counts.items() if count > 1
    )
    if duplicate_names:
        raise ValueError(
            "Duplicate component names in the catalogue: " + ", ".join(duplicate_names)
        )
