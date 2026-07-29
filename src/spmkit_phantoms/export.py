"""Lógica de exportación de phantoms."""

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from spmkit_phantoms.models import SurfacePhantom


def _calc_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_array_hash(array: np.ndarray) -> str:
    source = np.asarray(array)
    dtype = source.dtype.newbyteorder("<")
    normalized = np.ascontiguousarray(source.astype(dtype, copy=False))
    identity = json.dumps(
        {"dtype": dtype.str, "shape": list(normalized.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(identity + b"\0" + normalized.tobytes(order="C")).hexdigest()


def normalized_manifest_hash(manifest: dict[str, Any]) -> str:
    payload = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def export_bundle(phantom: SurfacePhantom, case_name: str, output_dir: Path) -> None:
    """Exporta el bundle (clean.npz + manifest.json) a una subcarpeta case_name."""
    
    bundle_dir = output_dir / case_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    npz_path = bundle_dir / "clean.npz"
    np.savez_compressed(
        npz_path,
        z_data=phantom.z_data,
        x_size_m=np.array([phantom.x_size_m], dtype=np.float64),
        y_size_m=np.array([phantom.y_size_m], dtype=np.float64),
        z_unit=np.array([phantom.z_unit], dtype=str),
        model_name=np.array([phantom.model_name], dtype=str)
    )
    
    artifact_hash = _calc_hash(npz_path)
    array_hash = canonical_array_hash(phantom.z_data)
    
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
        "dtype": phantom.z_data.dtype.str,
        "array_sha256": array_hash,
        "artifact_sha256": artifact_hash,
        "data_hash": array_hash,
    }
    manifest["manifest_sha256"] = normalized_manifest_hash(manifest)
    
    manifest_path = bundle_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def export_observed_bundle(
    phantom: "ObservedPhantom",
    case_name: str,
    output_dir: Path,
    rng_seed: int | None = None,
) -> None:
    """Exporta el bundle completo (clean, observed, masks, manifest)."""
    
    bundle_dir = output_dir / case_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Export clean
    clean_npz = bundle_dir / "clean.npz"
    np.savez_compressed(
        clean_npz,
        z_data=phantom.clean.z_data,
        x_size_m=np.array([phantom.clean.x_size_m], dtype=np.float64),
        y_size_m=np.array([phantom.clean.y_size_m], dtype=np.float64),
        z_unit=np.array([phantom.clean.z_unit], dtype=str),
        model_name=np.array([phantom.clean.model_name], dtype=str)
    )
    clean_artifact_hash = _calc_hash(clean_npz)
    clean_array_hash = canonical_array_hash(phantom.clean.z_data)
    
    # 2. Export observed
    obs_npz = bundle_dir / "observed.npz"
    np.savez_compressed(
        obs_npz,
        z_data=phantom.observed_z,
        x_size_m=np.array([phantom.clean.x_size_m], dtype=np.float64),
        y_size_m=np.array([phantom.clean.y_size_m], dtype=np.float64),
        z_unit=np.array([phantom.clean.z_unit], dtype=str),
        model_name=np.array([phantom.clean.model_name], dtype=str)
    )
    observed_artifact_hash = _calc_hash(obs_npz)
    observed_array_hash = canonical_array_hash(phantom.observed_z)
    
    # 3. Export masks if any
    masks_hash = None
    mask_array_hashes: dict[str, str] = {}
    if phantom.masks:
        masks_npz = bundle_dir / "masks.npz"
        np.savez_compressed(masks_npz, **phantom.masks)
        masks_hash = _calc_hash(masks_npz)
        mask_array_hashes = {
            name: canonical_array_hash(mask) for name, mask in sorted(phantom.masks.items())
        }
        
    # 4. Manifest
    manifest = {
        "schema_version": phantom.schema_version,
        "clean_model": phantom.clean.model_name,
        "clean_parameters": phantom.clean.original_parameters,
        "clean_array_sha256": clean_array_hash,
        "observed_array_sha256": observed_array_hash,
        "clean_artifact_sha256": clean_artifact_hash,
        "observed_artifact_sha256": observed_artifact_hash,
        "masks_artifact_sha256": masks_hash,
        "mask_array_sha256": mask_array_hashes,
        "clean_hash": clean_array_hash,
        "observed_hash": observed_array_hash,
        "masks_hash": masks_hash,
        "applied_corruptions": phantom.applied_corruptions,
        "rng_seed": rng_seed,
        "dimensions": phantom.observed_z.shape,
        "dtype": phantom.observed_z.dtype.str,
        "physical_scales": {
            "x_size_m": phantom.clean.x_size_m,
            "y_size_m": phantom.clean.y_size_m,
        },
        "units": phantom.clean.z_unit,
    }
    manifest["manifest_sha256"] = normalized_manifest_hash(manifest)
    
    manifest_path = bundle_dir / "corruption_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
