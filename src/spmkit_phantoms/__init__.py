"""spmkit-phantoms: Generador de ground truth analítico."""

from spmkit_phantoms.models import SurfacePhantom, ObservedPhantom
from spmkit_phantoms.surfaces import (
    flat_surface, inclined_plane, sinusoidal_surface, step_surface, gaussian_particles
)
from spmkit_phantoms.corruptions import (
    AdditiveGaussianNoise, LineOffsets, SlowLinearDrift, IsolatedSpikes, MissingLines
)
from spmkit_phantoms.export import export_bundle, export_observed_bundle
