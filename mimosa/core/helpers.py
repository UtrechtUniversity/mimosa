from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class ComponentConfig:
    """
    Configuration for a model component, including the module name and any options.
    """

    module: str
    options: Dict[str, Any] = field(
        default_factory=dict
    )  # Use field to avoid shared dictionary between instances
