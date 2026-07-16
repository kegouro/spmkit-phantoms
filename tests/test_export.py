"""Tests de exportación."""

import json
import numpy as np
from pathlib import Path
from spmkit_phantoms.surfaces import flat_surface
from spmkit_phantoms.export import export_bundle


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
