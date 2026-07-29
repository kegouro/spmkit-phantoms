"""Tests de exportación."""

import json
import numpy as np
from pathlib import Path
from spmkit_phantoms.surfaces import flat_surface
from spmkit_phantoms.corruptions import AdditiveGaussianNoise
from spmkit_phantoms.export import (
    canonical_array_hash,
    export_bundle,
    export_observed_bundle,
    normalized_manifest_hash,
)


def test_export_bundle(tmp_path: Path):
    surf = flat_surface((10, 10), 1e-6, 1e-6, height=5e-9)
    export_bundle(surf, "test_flat", tmp_path)
    
    bundle_dir = tmp_path / "test_flat"
    assert bundle_dir.exists()
    
    npz_path = bundle_dir / "clean.npz"
    json_path = bundle_dir / "manifest.json"
    
    assert npz_path.exists()
    assert json_path.exists()
    
    # Check npz load
    loaded = np.load(npz_path)
    assert np.all(loaded["z_data"] == surf.z_data)
    assert loaded["x_size_m"][0] == 1e-6
    assert loaded["y_size_m"][0] == 1e-6
    assert loaded["z_unit"][0] == "m"
    assert loaded["model_name"][0] == "flat_surface"
    
    # Check JSON
    with json_path.open() as f:
        manifest = json.load(f)
        
    assert manifest["model"] == "flat_surface"
    assert "data_hash" in manifest
    assert len(manifest["data_hash"]) == 64
    assert manifest["data_hash"] == canonical_array_hash(surf.z_data)
    assert len(manifest["artifact_sha256"]) == 64
    manifest_hash = manifest.pop("manifest_sha256")
    assert manifest_hash == normalized_manifest_hash(manifest)


def test_canonical_array_hash_normalizes_layout_and_byte_order():
    base = np.arange(12, dtype="<f8").reshape(3, 4)
    fortran = np.asfortranarray(base)
    big_endian = base.astype(">f8")

    assert canonical_array_hash(base) == canonical_array_hash(fortran)
    assert canonical_array_hash(base) == canonical_array_hash(big_endian)
    assert canonical_array_hash(base) != canonical_array_hash(base.reshape(4, 3))


def test_observed_manifest_records_seed_and_canonical_hashes(tmp_path: Path):
    clean = flat_surface((8, 8), 1e-6, 1e-6)
    observed = AdditiveGaussianNoise(1e-9).apply(clean, np.random.default_rng(17))
    export_observed_bundle(observed, "observed", tmp_path, rng_seed=17)

    with (tmp_path / "observed" / "corruption_manifest.json").open() as handle:
        manifest = json.load(handle)

    assert manifest["rng_seed"] == 17
    assert manifest["clean_array_sha256"] == canonical_array_hash(clean.z_data)
    assert manifest["observed_array_sha256"] == canonical_array_hash(observed.observed_z)
    manifest_hash = manifest.pop("manifest_sha256")
    assert manifest_hash == normalized_manifest_hash(manifest)
