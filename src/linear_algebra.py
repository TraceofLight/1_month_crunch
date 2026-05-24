"""Linear algebra utilities for matrix transforms, eigensolvers, and SVD."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class PowerIterationResult:
    """Result returned by the Power Iteration eigensolver."""

    eigenvalue: float
    eigenvector: np.ndarray
    iterations: int
    converged: bool


@dataclass(frozen=True)
class SVDCompressionResult:
    """Compressed image reconstruction and retained singular-value metadata."""

    reconstructed: np.ndarray
    singular_values: np.ndarray
    rank_used: int
    energy_ratio: float


def unit_circle(num_points: int = 100) -> np.ndarray:
    """Return points on the unit circle as an array with shape ``(n, 2)``."""

    if num_points < 3:
        raise ValueError("num_points must be at least 3")
    theta = np.linspace(0.0, 2.0 * np.pi, num_points, endpoint=False)
    return np.column_stack((np.cos(theta), np.sin(theta)))


def rotation_matrix(theta: float) -> np.ndarray:
    """Return the 2D rotation matrix ``R(theta)``."""

    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    return np.array([[cos_t, -sin_t], [sin_t, cos_t]], dtype=float)


def scaling_matrix(sx: float, sy: float) -> np.ndarray:
    """Return the 2D scaling matrix ``diag(sx, sy)``."""

    return np.array([[sx, 0.0], [0.0, sy]], dtype=float)


def shear_matrix(k: float) -> np.ndarray:
    """Return the horizontal shear matrix ``[[1, k], [0, 1]]``."""

    return np.array([[1.0, k], [0.0, 1.0]], dtype=float)


def apply_transform(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Apply a 2D linear transform to row-vector points.

    The formula is ``p' = A p``. Because points are stored as row vectors,
    this is implemented as ``points @ A.T``.
    """

    points_array = np.asarray(points, dtype=float)
    matrix_array = np.asarray(matrix, dtype=float)
    if points_array.ndim != 2 or points_array.shape[1] != 2:
        raise ValueError("points must have shape (n, 2)")
    if matrix_array.shape != (2, 2):
        raise ValueError("matrix must have shape (2, 2)")
    return points_array @ matrix_array.T


def polygon_area(points: np.ndarray) -> float:
    """Compute polygon area with the shoelace formula.

    ``area = 1/2 * |sum(x_i y_{i+1} - y_i x_{i+1})|``
    """

    points_array = np.asarray(points, dtype=float)
    if points_array.ndim != 2 or points_array.shape[1] != 2:
        raise ValueError("points must have shape (n, 2)")
    x_values = points_array[:, 0]
    y_values = points_array[:, 1]
    return float(
        0.5
        * abs(
            np.dot(x_values, np.roll(y_values, -1))
            - np.dot(y_values, np.roll(x_values, -1))
        )
    )


def transform_area_comparison(
    matrix: np.ndarray, points: np.ndarray | None = None
) -> dict[str, float]:
    """Compare ``|det(A)|`` with the measured polygon area ratio."""

    base_points = unit_circle(720) if points is None else np.asarray(points, dtype=float)
    transformed = apply_transform(base_points, matrix)
    before_area = polygon_area(base_points)
    after_area = polygon_area(transformed)
    determinant = float(np.linalg.det(matrix))
    area_ratio = after_area / before_area
    det_abs = abs(determinant)
    denominator = max(det_abs, np.finfo(float).eps)
    relative_error = abs(area_ratio - det_abs) / denominator
    return {
        "determinant": determinant,
        "abs_determinant": det_abs,
        "area_before": before_area,
        "area_after": after_area,
        "area_ratio": area_ratio,
        "relative_error": relative_error,
    }


def power_iteration(
    matrix: np.ndarray,
    max_iter: int = 1_000,
    tol: float = 1e-6,
    seed: int = 42,
) -> PowerIterationResult:
    """Estimate the dominant eigenpair using Power Iteration.

    Starting from a fixed random vector ``v_0``, the algorithm repeats
    ``v_{t+1} = A v_t / ||A v_t||`` and estimates the eigenvalue with the
    Rayleigh quotient ``lambda = v^T A v / v^T v``.
    """

    matrix_array = np.asarray(matrix, dtype=float)
    if matrix_array.ndim != 2 or matrix_array.shape[0] != matrix_array.shape[1]:
        raise ValueError("matrix must be square")
    rng = np.random.default_rng(seed)
    vector = rng.normal(size=matrix_array.shape[0])
    vector = vector / np.linalg.norm(vector)

    converged = False
    iterations = 0
    for iteration in range(1, max_iter + 1):
        next_vector = matrix_array @ vector
        norm = np.linalg.norm(next_vector)
        if norm == 0.0:
            raise ValueError("matrix maps the iteration vector to zero")
        next_vector = next_vector / norm
        sign_invariant_delta = min(
            np.linalg.norm(next_vector - vector),
            np.linalg.norm(next_vector + vector),
        )
        vector = next_vector
        iterations = iteration
        if sign_invariant_delta < tol:
            converged = True
            break

    eigenvalue = float(vector @ matrix_array @ vector / (vector @ vector))
    return PowerIterationResult(
        eigenvalue=eigenvalue,
        eigenvector=vector,
        iterations=iterations,
        converged=converged,
    )


def compress_image_svd(image: np.ndarray, k: int) -> SVDCompressionResult:
    """Reconstruct a grayscale image using the top ``k`` singular values."""

    image_array = np.asarray(image, dtype=float)
    if image_array.ndim != 2:
        raise ValueError("image must be a 2D grayscale array")
    if k <= 0:
        raise ValueError("k must be positive")

    u_matrix, singular_values, vt_matrix = np.linalg.svd(image_array, full_matrices=False)
    rank_used = min(int(k), singular_values.size)
    reconstructed = (
        u_matrix[:, :rank_used]
        @ np.diag(singular_values[:rank_used])
        @ vt_matrix[:rank_used, :]
    )
    total_energy = float(np.sum(singular_values**2))
    kept_energy = float(np.sum(singular_values[:rank_used] ** 2))
    energy_ratio = 1.0 if total_energy == 0.0 else kept_energy / total_energy
    return SVDCompressionResult(
        reconstructed=reconstructed,
        singular_values=singular_values,
        rank_used=rank_used,
        energy_ratio=energy_ratio,
    )


def plot_transformation(
    matrix: np.ndarray,
    title: str,
    output_path: str | Path | None = None,
    points: np.ndarray | None = None,
) -> tuple[plt.Figure, dict[str, float]]:
    """Plot original and transformed unit-circle points in one figure."""

    base_points = unit_circle(360) if points is None else np.asarray(points, dtype=float)
    transformed = apply_transform(base_points, matrix)
    stats = transform_area_comparison(matrix, base_points)

    figure, axis = plt.subplots(figsize=(6, 6))
    closed_base = np.vstack((base_points, base_points[0]))
    closed_transformed = np.vstack((transformed, transformed[0]))
    axis.plot(closed_base[:, 0], closed_base[:, 1], label="Before: unit circle", lw=2)
    axis.plot(
        closed_transformed[:, 0],
        closed_transformed[:, 1],
        label="After: transformed",
        lw=2,
    )
    axis.axhline(0.0, color="black", lw=0.8, alpha=0.5)
    axis.axvline(0.0, color="black", lw=0.8, alpha=0.5)
    axis.set_aspect("equal", adjustable="box")
    axis.set_title(title)
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.legend(loc="upper right")
    axis.grid(True, alpha=0.25)
    text = (
        f"det={stats['determinant']:.4f}\n"
        f"area ratio={stats['area_ratio']:.4f}\n"
        f"error={stats['relative_error'] * 100:.4f}%"
    )
    axis.text(0.03, 0.03, text, transform=axis.transAxes, va="bottom")
    figure.tight_layout()
    if output_path is not None:
        save_figure(figure, output_path)
    return figure, stats


def plot_svd_comparison(
    image: np.ndarray,
    ks: Iterable[int] = (10, 50, 100),
    output_path: str | Path | None = None,
) -> tuple[plt.Figure, list[SVDCompressionResult]]:
    """Plot the original image and SVD reconstructions for several ranks."""

    image_array = np.asarray(image, dtype=float)
    results = [compress_image_svd(image_array, k) for k in ks]
    figure, axes = plt.subplots(1, len(results) + 1, figsize=(4 * (len(results) + 1), 4))
    axes[0].imshow(image_array, cmap="gray")
    axes[0].set_title("Original")
    axes[0].axis("off")

    for axis, requested_k, result in zip(axes[1:], ks, results):
        axis.imshow(result.reconstructed, cmap="gray")
        axis.set_title(
            f"k={requested_k}\nused={result.rank_used}, energy={result.energy_ratio:.3f}"
        )
        axis.axis("off")

    figure.tight_layout()
    if output_path is not None:
        save_figure(figure, output_path)
    return figure, results


def save_figure(figure: plt.Figure, output_path: str | Path) -> None:
    """Create the parent directory and save a Matplotlib figure."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160, bbox_inches="tight")
