"""Pruebas para las corrupciones y artefactos."""

import numpy as np
from spmkit_phantoms.surfaces import flat_surface
from spmkit_phantoms.corruptions import (
    AdditiveGaussianNoise,
    LineOffsets,
    SlowLinearDrift,
    IsolatedSpikes,
    MissingLines
)

def test_zero_intensity_is_identity():
    clean = flat_surface((10, 10), 1e-6, 1e-6, height=0.0)
    rng = np.random.default_rng(42)
    
    c1 = AdditiveGaussianNoise(0.0).apply(clean, rng)
    c2 = LineOffsets(0.0).apply(clean, rng)
    c3 = SlowLinearDrift(0.0).apply(clean, rng)
    c4 = IsolatedSpikes(0.0, 1.0).apply(clean, rng)
    c5 = MissingLines(0.0).apply(clean, rng)
    
    assert np.all(c1.observed_z == clean.z_data)
    assert np.all(c2.observed_z == clean.z_data)
    assert np.all(c3.observed_z == clean.z_data)
    assert np.all(c4.observed_z == clean.z_data)
    assert np.all(c5.observed_z == clean.z_data)
    
    # Check that clean array is exactly the same memory object or identical
    # The models implementation uses .copy() if 0.0 to be safe, but data is identical
    assert c1.clean is clean


def test_additive_gaussian_noise_convergence():
    clean = flat_surface((1000, 1000), 1e-6, 1e-6, height=0.0)
    rng = np.random.default_rng(42)
    
    sigma = 1e-9
    obs = AdditiveGaussianNoise(sigma).apply(clean, rng)
    
    # Should not mutate clean
    assert np.all(clean.z_data == 0.0)
    
    # Check std deviation approaches sigma
    assert np.isclose(np.std(obs.observed_z), sigma, rtol=0.05)


def test_reproducibility():
    clean = flat_surface((10, 10), 1e-6, 1e-6, height=0.0)
    
    rng1 = np.random.default_rng(123)
    obs1 = IsolatedSpikes(0.5, 1e-9).apply(clean, rng1)
    
    rng2 = np.random.default_rng(123)
    obs2 = IsolatedSpikes(0.5, 1e-9).apply(clean, rng2)
    
    assert np.all(obs1.observed_z == obs2.observed_z)


def test_composition():
    clean = flat_surface((10, 10), 1e-6, 1e-6, height=0.0)
    rng = np.random.default_rng(42)
    
    obs1 = AdditiveGaussianNoise(1e-9).apply(clean, rng)
    obs2 = SlowLinearDrift(0.1).apply(obs1, rng)
    
    assert len(obs2.applied_corruptions) == 2
    assert obs2.applied_corruptions[0]["name"] == "AdditiveGaussianNoise"
    assert obs2.applied_corruptions[1]["name"] == "SlowLinearDrift"
    assert obs2.clean is clean


def test_masks_correctness():
    clean = flat_surface((10, 10), 1e-6, 1e-6, height=0.0)
    rng = np.random.default_rng(42)
    
    obs = IsolatedSpikes(0.5, 1e-9).apply(clean, rng)
    mask = obs.masks["spikes_mask"]
    
    assert np.all(np.abs(obs.observed_z[mask]) == 1e-9)
    assert np.all(obs.observed_z[~mask] == 0.0)


def test_line_offsets():
    clean = flat_surface((10, 10), 1e-6, 1e-6, height=0.0)
    rng = np.random.default_rng(42)
    obs = LineOffsets(1e-9).apply(clean, rng)
    
    # Check that each row is constant
    assert np.all(obs.observed_z[:, 0:1] == obs.observed_z)


def test_missing_lines():
    clean = flat_surface((10, 10), 1e-6, 1e-6, height=0.0)
    # Add a slope to x and y so lines are distinct
    clean.z_data[:] = np.arange(10).reshape(10, 1) * 1.0
    
    rng = np.random.default_rng(42)
    obs = MissingLines(0.5).apply(clean, rng)
    
    mask = obs.masks["missing_lines_mask"]
    for i in range(1, 10):
        if mask[i, 0]:
            assert np.all(obs.observed_z[i, :] == obs.observed_z[i-1, :])
