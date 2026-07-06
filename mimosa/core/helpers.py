from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class ComponentConfig:
    """
    Configuration for a model component, including the module name and any options.
    """

    module: str = ""
    options: Dict[str, Any] = field(
        default_factory=dict
    )  # Use field to avoid shared dictionary between instances


@dataclass(frozen=True)
class ModelContext:
    components: Dict[str, ComponentConfig]

    def module(self, name: str) -> str:
        return self.components[name].module

    def options(self, name: str) -> Dict[str, Any]:
        return self.components[name].options if name in self.components else {}

    def option(self, component: str, option: str, default=None):
        return self.options(component).get(option, default)
