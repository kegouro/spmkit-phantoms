"""CLI básico para generar phantoms de prueba."""

import argparse
from pathlib import Path

from spmkit_phantoms.surfaces import flat_surface, inclined_plane, sinusoidal_surface
from spmkit_phantoms.export import export_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="SPM Phantoms Generator")
    parser.add_argument("--outdir", type=Path, default=Path("."), help="Directorio de salida")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para corrupciones")
    args = parser.parse_args()
    
    # Generar algunos phantoms básicos
    print(f"Generando phantoms en {args.outdir}...")
    
    # 1. Flat
    s1 = flat_surface((256, 256), 10e-6, 10e-6, height=0.0)
    export_bundle(s1, "flat_0nm", args.outdir)
    
    # 2. Inclined + Noise
    rng = __import__('numpy').random.default_rng(args.seed)
    s2 = inclined_plane((256, 256), 10e-6, 10e-6, slope_x=0.1, slope_y=0.0)
    
    from spmkit_phantoms.corruptions import AdditiveGaussianNoise, IsolatedSpikes
    from spmkit_phantoms.export import export_observed_bundle
    
    obs = AdditiveGaussianNoise(1e-9).apply(s2, rng)
    obs = IsolatedSpikes(0.01, 10e-9).apply(obs, rng)
    
    export_observed_bundle(obs, "inclined_noisy", args.outdir, rng_seed=args.seed)
    
    print("Done.")

if __name__ == "__main__":
    main()
