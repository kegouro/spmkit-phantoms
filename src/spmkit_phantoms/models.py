"""Modelos de datos para phantoms SPM."""

from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass(frozen=True)
class SurfacePhantom:
    """Modelo inmutable de una superficie matemática pura."""
    
    z_data: np.ndarray
    x_size_m: float
    y_size_m: float
    z_unit: str
    model_name: str
    original_parameters: dict[str, Any]
    seed: int | None = None
    schema_version: str = "1.0"


@dataclass(frozen=True)
class ObservedPhantom:
    """Modelo inmutable de una superficie observada (con ruido/artefactos)."""
    
    clean: SurfacePhantom
    observed_z: np.ndarray
    applied_corruptions: list[dict[str, Any]]
    masks: dict[str, np.ndarray] = field(default_factory=dict)
    schema_version: str = "1.0"

