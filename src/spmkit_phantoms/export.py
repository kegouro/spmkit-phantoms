"""Lógica de exportación de phantoms."""

import hashlib
import json
from pathlib import Path

import numpy as np
from spmkit_phantoms.models import SurfacePhantom


def _calc_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def export_bundle(phantom: SurfacePhantom, case_name: str, output_dir: Path) -> None:
    """Exporta el bundle (clean.npz + manifest.json) a una subcarpeta case_name."""
    
    bundle_dir = output_dir / case_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    npz_path = bundle_dir / "clean.npz"
    np.savez_compressed(npz_path, z_data=phantom.z_data)
    
    file_hash = _calc_hash(npz_path)
    
    manifest = {
        "model": phantom.model_name,
        "parameters": phantom.original_parameters,
        "dimensions": phantom.z_data.shape,
        "physical_scales": {
            "x_size_m": phantom.x_size_m,
            "y_size_m": phantom.y_size_m,
        },
        "units": phantom.z_unit,
        "seed": phantom.seed,
        "schema_version": phantom.schema_version,
        "data_hash": file_hash,
    }
    
    manifest_path = bundle_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def export_observed_bundle(phantom: "ObservedPhantom", case_name: str, output_dir: Path) -> None:
    """Exporta el bundle completo (clean, observed, masks, manifest)."""
    
    bundle_dir = output_dir / case_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Export clean
    clean_npz = bundle_dir / "clean.npz"
    np.savez_compressed(clean_npz, z_data=phantom.clean.z_data)
    clean_hash = _calc_hash(clean_npz)
    
    # 2. Export observed
    obs_npz = bundle_dir / "observed.npz"
    np.savez_compressed(obs_npz, z_data=phantom.observed_z)
    obs_hash = _calc_hash(obs_npz)
    
    # 3. Export masks if any
    masks_hash = None
    if phantom.masks:
        masks_npz = bundle_dir / "masks.npz"
        np.savez_compressed(masks_npz, **phantom.masks)
        masks_hash = _calc_hash(masks_npz)
        
    # 4. Manifest
    manifest = {
        "schema_version": phantom.schema_version,
        "clean_model": phantom.clean.model_name,
        "clean_parameters": phantom.clean.original_parameters,
        "clean_hash": clean_hash,
        "observed_hash": obs_hash,
        "masks_hash": masks_hash,
        "applied_corruptions": phantom.applied_corruptions,
        "dimensions": phantom.observed_z.shape,
        "physical_scales": {
            "x_size_m": phantom.clean.x_size_m,
            "y_size_m": phantom.clean.y_size_m,
        },
        "units": phantom.clean.z_unit,
    }
    
    manifest_path = bundle_dir / "corruption_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

