"""Transformaciones de ruido y artefactos."""

from typing import Protocol, Any
import numpy as np

from spmkit_phantoms.models import SurfacePhantom, ObservedPhantom


class Corruption(Protocol):
    def apply(self, phantom: SurfacePhantom | ObservedPhantom, rng: np.random.Generator) -> ObservedPhantom:
        ...


def _get_z(phantom: SurfacePhantom | ObservedPhantom) -> np.ndarray:
    return phantom.observed_z if isinstance(phantom, ObservedPhantom) else phantom.z_data


def _wrap_observed(
    original: SurfacePhantom | ObservedPhantom,
    new_z: np.ndarray,
    corruption_record: dict[str, Any],
    new_masks: dict[str, np.ndarray] | None = None
) -> ObservedPhantom:
    if isinstance(original, ObservedPhantom):
        clean = original.clean
        applied = list(original.applied_corruptions) + [corruption_record]
        masks = dict(original.masks)
    else:
        clean = original
        applied = [corruption_record]
        masks = {}
        
    if new_masks:
        masks.update(new_masks)
        
    return ObservedPhantom(
        clean=clean,
        observed_z=new_z,
        applied_corruptions=applied,
        masks=masks
    )


class AdditiveGaussianNoise:
    """Añade ruido estocástico puro (SNR documentado)."""
    
    def __init__(self, sigma: float):
        self.sigma = sigma
        
    def apply(self, phantom: SurfacePhantom | ObservedPhantom, rng: np.random.Generator) -> ObservedPhantom:
        z = _get_z(phantom)
        
        if self.sigma == 0.0:
            new_z = z.copy()
        else:
            noise = rng.normal(loc=0.0, scale=self.sigma, size=z.shape)
            new_z = z + noise
            
        record = {
            "name": "AdditiveGaussianNoise",
            "parameters": {"sigma": self.sigma}
        }
        return _wrap_observed(phantom, new_z, record)


class LineOffsets:
    """Añade saltos constantes de altura independientes por cada fila Y."""
    
    def __init__(self, sigma: float):
        self.sigma = sigma
        
    def apply(self, phantom: SurfacePhantom | ObservedPhantom, rng: np.random.Generator) -> ObservedPhantom:
        z = _get_z(phantom)
        
        if self.sigma == 0.0:
            new_z = z.copy()
        else:
            # Una offset por cada línea (eje Y)
            ny, _ = z.shape
            offsets = rng.normal(loc=0.0, scale=self.sigma, size=(ny, 1))
            new_z = z + offsets
            
        record = {
            "name": "LineOffsets",
            "parameters": {"sigma": self.sigma}
        }
        return _wrap_observed(phantom, new_z, record)


class SlowLinearDrift:
    """Simula una deriva lineal en la posición del piezo."""
    
    def __init__(self, slope_y: float):
        self.slope_y = slope_y
        
    def apply(self, phantom: SurfacePhantom | ObservedPhantom, rng: np.random.Generator) -> ObservedPhantom:
        z = _get_z(phantom)
        
        if self.slope_y == 0.0:
            new_z = z.copy()
        else:
            ny, nx = z.shape
            # Generar rampa de drift lenta sobre el eje lento Y
            # Suponiendo Y es el eje de avance (filas)
            y_indices = np.arange(ny).reshape(ny, 1)
            drift = self.slope_y * y_indices
            new_z = z + drift
            
        record = {
            "name": "SlowLinearDrift",
            "parameters": {"slope_y": self.slope_y}
        }
        return _wrap_observed(phantom, new_z, record)


class IsolatedSpikes:
    """Añade picos extremos (positivos o negativos) en coordenadas aleatorias aisladas."""
    
    def __init__(self, fraction: float, amplitude: float):
        self.fraction = fraction
        self.amplitude = amplitude
        
    def apply(self, phantom: SurfacePhantom | ObservedPhantom, rng: np.random.Generator) -> ObservedPhantom:
        z = _get_z(phantom)
        
        if self.fraction == 0.0 or self.amplitude == 0.0:
            new_z = z.copy()
            mask = np.zeros(z.shape, dtype=bool)
        else:
            new_z = z.copy()
            mask = rng.random(size=z.shape) < self.fraction
            signs = rng.choice([-1.0, 1.0], size=z.shape)
            new_z[mask] += self.amplitude * signs[mask]
            
        record = {
            "name": "IsolatedSpikes",
            "parameters": {"fraction": self.fraction, "amplitude": self.amplitude}
        }
        return _wrap_observed(phantom, new_z, record, {"spikes_mask": mask})


class MissingLines:
    """Simula el congelamiento de líneas (la línea repite la anterior)."""
    
    def __init__(self, fraction: float):
        self.fraction = fraction
        
    def apply(self, phantom: SurfacePhantom | ObservedPhantom, rng: np.random.Generator) -> ObservedPhantom:
        z = _get_z(phantom)
        ny, nx = z.shape
        
        if self.fraction == 0.0:
            new_z = z.copy()
            mask = np.zeros(z.shape, dtype=bool)
        else:
            new_z = z.copy()
            mask = np.zeros(z.shape, dtype=bool)
            
            line_lost = rng.random(size=ny) < self.fraction
            for i in range(1, ny):
                if line_lost[i]:
                    new_z[i, :] = new_z[i-1, :]
                    mask[i, :] = True
                    
        record = {
            "name": "MissingLines",
            "parameters": {"fraction": self.fraction}
        }
        return _wrap_observed(phantom, new_z, record, {"missing_lines_mask": mask})
