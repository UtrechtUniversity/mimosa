"""Construction and configuration mechanics for model components."""

from dataclasses import dataclass
from typing import Callable, Dict, Optional

from mimosa.common.utils import load_from_registry

from .helpers import ComponentConfig, ModelContext


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

    def read_config(self, model_structure: dict) -> ComponentConfig:
        """Read this component's module choice and options from model structure."""
        if self.modules is not None:
            return ComponentConfig(
                module=model_structure[f"{self.name} module"],
                options=model_structure.get(f"{self.name} module options", {}),
            )

        return ComponentConfig(
            options=model_structure.get(f"{self.name} options", {}),
        )

    def build(self, model, context: ModelContext):
        """Add this component's model objects and return its constraints."""
        get_constraints = self.get_constraints
        if self.modules is not None:
            get_constraints = load_from_registry(context.module(self.name), self.modules)

        return get_constraints(model, context)


def fixed_component(name: str, get_constraints: Callable) -> ComponentDefinition:
    """Define a component that is always included."""
    return ComponentDefinition(name=name, get_constraints=get_constraints)


def selectable_component(
    name: str, modules: Dict[str, Callable]
) -> ComponentDefinition:
    """Define a component selected through ``<name> module`` in the config."""
    return ComponentDefinition(name=name, modules=modules)
