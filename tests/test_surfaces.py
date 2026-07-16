"""Tests de generación de superficies matemáticas puros."""

import numpy as np
from spmkit_phantoms.surfaces import (
    flat_surface,
    inclined_plane,
    sinusoidal_surface,
    step_surface,
    gaussian_particles
)


def test_flat_surface():
    surf = flat_surface((10, 10), 1e-6, 1e-6, height=5e-9)
    assert surf.z_data.shape == (10, 10)
    assert np.all(surf.z_data == 5e-9)
    assert surf.x_size_m == 1e-6


def test_inclined_plane():
    # dx = 1e-6. slope_x = 0.1 -> delta Z across x should be 0.1 * 1e-6
    surf = inclined_plane((10, 10), 1e-6, 1e-6, slope_x=0.1, slope_y=0.0)
    
    # Check max diff in x
    z_min = np.min(surf.z_data[0, :])
    z_max = np.max(surf.z_data[0, :])
    
    assert np.isclose(z_max - z_min, 0.1 * 1e-6)
    # Check y is flat
    assert np.all(surf.z_data[0, :] == surf.z_data[1, :])


def test_sinusoidal_surface():
    surf = sinusoidal_surface((100, 100), 10e-6, 10e-6, amplitude=1e-9, period_x=5e-6, period_y=5e-6)
    assert np.isclose(np.max(surf.z_data), 1e-9)
    assert np.isclose(np.min(surf.z_data), -1e-9)


def test_step_surface():
    surf = step_surface((10, 10), 1e-6, 1e-6, step_height=10e-9)
    assert surf.z_data[0, 0] == 0.0
    assert surf.z_data[0, -1] == 10e-9


def test_gaussian_particles_determinism():
    surf1 = gaussian_particles((50, 50), 1e-6, 1e-6, n_particles=5, sigma=1e-7, amplitude=2e-9, seed=42)
    surf2 = gaussian_particles((50, 50), 1e-6, 1e-6, n_particles=5, sigma=1e-7, amplitude=2e-9, seed=42)
    
    assert np.all(surf1.z_data == surf2.z_data)
    assert np.max(surf1.z_data) > 0
