"""Generadores de superficies analíticas SPM."""

import numpy as np
from spmkit_phantoms.models import SurfacePhantom


def flat_surface(
    shape: tuple[int, int], x_size_m: float, y_size_m: float, height: float = 0.0
) -> SurfacePhantom:
    """Genera un plano exactamente plano a una altura dada."""
    z_data = np.full(shape, height, dtype=np.float64)
    return SurfacePhantom(
        z_data=z_data,
        x_size_m=x_size_m,
        y_size_m=y_size_m,
        z_unit="m",
        model_name="flat_surface",
        original_parameters={"height": height},
    )


def inclined_plane(
    shape: tuple[int, int],
    x_size_m: float,
    y_size_m: float,
    slope_x: float,
    slope_y: float,
    z_offset: float = 0.0,
) -> SurfacePhantom:
    """Genera un plano inclinado con pendientes conocidas (dz/dx, dz/dy)."""
    ny, nx = shape
    # Vectores de coordenadas físicas (origen en el centro)
    x = np.linspace(-x_size_m / 2, x_size_m / 2, nx, dtype=np.float64)
    y = np.linspace(-y_size_m / 2, y_size_m / 2, ny, dtype=np.float64)
    xx, yy = np.meshgrid(x, y)
    
    z_data = slope_x * xx + slope_y * yy + z_offset
    
    return SurfacePhantom(
        z_data=z_data,
        x_size_m=x_size_m,
        y_size_m=y_size_m,
        z_unit="m",
        model_name="inclined_plane",
        original_parameters={"slope_x": slope_x, "slope_y": slope_y, "z_offset": z_offset},
    )


def sinusoidal_surface(
    shape: tuple[int, int],
    x_size_m: float,
    y_size_m: float,
    amplitude: float,
    period_x: float,
    period_y: float,
) -> SurfacePhantom:
    """Genera una superficie sinusoidal 2D. (z = A * sin(2*pi*x/Tx) * sin(2*pi*y/Ty))."""
    ny, nx = shape
    x = np.linspace(0, x_size_m, nx, endpoint=False, dtype=np.float64)
    y = np.linspace(0, y_size_m, ny, endpoint=False, dtype=np.float64)
    xx, yy = np.meshgrid(x, y)
    
    kx = 2 * np.pi / period_x if period_x > 0 else 0
    ky = 2 * np.pi / period_y if period_y > 0 else 0
    
    z_data = amplitude * np.sin(kx * xx) * np.sin(ky * yy)
    
    return SurfacePhantom(
        z_data=z_data,
        x_size_m=x_size_m,
        y_size_m=y_size_m,
        z_unit="m",
        model_name="sinusoidal_surface",
        original_parameters={
            "amplitude": amplitude,
            "period_x": period_x,
            "period_y": period_y,
        },
    )


def step_surface(
    shape: tuple[int, int],
    x_size_m: float,
    y_size_m: float,
    step_height: float,
    x_split_ratio: float = 0.5,
) -> SurfacePhantom:
    """Genera un escalón puro (mitad izquierda 0, mitad derecha step_height)."""
    ny, nx = shape
    z_data = np.zeros(shape, dtype=np.float64)
    split_col = int(nx * x_split_ratio)
    z_data[:, split_col:] = step_height
    
    return SurfacePhantom(
        z_data=z_data,
        x_size_m=x_size_m,
        y_size_m=y_size_m,
        z_unit="m",
        model_name="step_surface",
        original_parameters={"step_height": step_height, "x_split_ratio": x_split_ratio},
    )


def gaussian_particles(
    shape: tuple[int, int],
    x_size_m: float,
    y_size_m: float,
    n_particles: int,
    sigma: float,
    amplitude: float,
    seed: int,
) -> SurfacePhantom:
    """Genera un conjunto de partículas gaussianas en posiciones aleatorias pero deterministas."""
    ny, nx = shape
    x = np.linspace(0, x_size_m, nx, dtype=np.float64)
    y = np.linspace(0, y_size_m, ny, dtype=np.float64)
    xx, yy = np.meshgrid(x, y)
    
    z_data = np.zeros(shape, dtype=np.float64)
    
    rng = np.random.default_rng(seed)
    
    for _ in range(n_particles):
        px = rng.uniform(0, x_size_m)
        py = rng.uniform(0, y_size_m)
        
        particle = amplitude * np.exp(-(((xx - px) ** 2) + ((yy - py) ** 2)) / (2 * sigma ** 2))
        z_data += particle
        
    return SurfacePhantom(
        z_data=z_data,
        x_size_m=x_size_m,
        y_size_m=y_size_m,
        z_unit="m",
        model_name="gaussian_particles",
        original_parameters={
            "n_particles": n_particles,
            "sigma": sigma,
            "amplitude": amplitude,
        },
        seed=seed,
    )
