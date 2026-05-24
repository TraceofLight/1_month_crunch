"""Calculus utilities for numerical differentiation and gradient plots."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np


ScalarFunction = Callable[[float], float]
VectorFunction = Callable[[np.ndarray], float]


def central_difference(function: ScalarFunction, x_value: float, h: float = 1e-5) -> float:
    """Approximate ``f'(x)`` with the centered difference formula.

    ``f'(x) ~= (f(x + h) - f(x - h)) / (2h)``
    """

    if h <= 0.0:
        raise ValueError("h must be positive")
    return float((function(x_value + h) - function(x_value - h)) / (2.0 * h))


def numerical_gradient(
    function: VectorFunction,
    point: np.ndarray,
    h: float = 1e-5,
) -> np.ndarray:
    """Approximate the gradient of a scalar function at ``point``."""

    if h <= 0.0:
        raise ValueError("h must be positive")
    point_array = np.asarray(point, dtype=float)
    gradient = np.zeros_like(point_array, dtype=float)
    for index in range(point_array.size):
        plus = point_array.copy()
        minus = point_array.copy()
        plus[index] += h
        minus[index] -= h
        gradient[index] = (function(plus) - function(minus)) / (2.0 * h)
    return gradient


def quadratic_2d(point: np.ndarray) -> float:
    """Return ``f(x, y) = x^2 + y^2`` for a 2D point."""

    point_array = np.asarray(point, dtype=float)
    return float(point_array[0] ** 2 + point_array[1] ** 2)


def quadratic_2d_gradient(point: np.ndarray) -> np.ndarray:
    """Return the analytic gradient ``grad f = [2x, 2y]``."""

    point_array = np.asarray(point, dtype=float)
    return np.array([2.0 * point_array[0], 2.0 * point_array[1]], dtype=float)


def plot_gradient_field(
    output_path: str | Path | None = None,
    xlim: tuple[float, float] = (-4.0, 4.0),
    ylim: tuple[float, float] = (-4.0, 4.0),
    contour_density: int = 160,
    arrow_density: int = 9,
) -> plt.Figure:
    """Draw contours of ``x^2 + y^2`` with perpendicular gradient arrows."""

    x_values = np.linspace(xlim[0], xlim[1], contour_density)
    y_values = np.linspace(ylim[0], ylim[1], contour_density)
    grid_x, grid_y = np.meshgrid(x_values, y_values)
    grid_z = grid_x**2 + grid_y**2

    arrow_x = np.linspace(xlim[0], xlim[1], arrow_density)
    arrow_y = np.linspace(ylim[0], ylim[1], arrow_density)
    quiver_x, quiver_y = np.meshgrid(arrow_x, arrow_y)
    quiver_u = 2.0 * quiver_x
    quiver_v = 2.0 * quiver_y

    figure, axis = plt.subplots(figsize=(7, 6))
    contours = axis.contour(grid_x, grid_y, grid_z, levels=12, cmap="viridis")
    axis.clabel(contours, inline=True, fontsize=8)
    axis.quiver(
        quiver_x,
        quiver_y,
        quiver_u,
        quiver_v,
        color="crimson",
        angles="xy",
        scale_units="xy",
        scale=12,
        width=0.004,
    )
    axis.set_title("Gradient field of f(x, y)=x^2+y^2")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.2)
    figure.tight_layout()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=160, bbox_inches="tight")
    return figure
