"""Gradient-based optimizers and convergence-path visualization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

import matplotlib.pyplot as plt
import numpy as np


Objective = Callable[[np.ndarray], float]
Gradient = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True)
class OptimizationResult:
    """Path and final state returned by an optimizer."""

    path: np.ndarray
    values: np.ndarray

    @property
    def final_point(self) -> np.ndarray:
        """Return the final point in the optimization path."""

        return self.path[-1]

    @property
    def final_value(self) -> float:
        """Return the final objective value."""

        return float(self.values[-1])


class VanillaGD:
    """Vanilla gradient descent with update ``theta <- theta - lr * grad``."""

    def __init__(self, lr: float) -> None:
        """Create a gradient descent optimizer."""

        if lr <= 0.0:
            raise ValueError("lr must be positive")
        self.lr = float(lr)

    def step(self, point: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        """Return one vanilla gradient descent update."""

        return np.asarray(point, dtype=float) - self.lr * np.asarray(gradient, dtype=float)

    def optimize(
        self,
        objective: Objective,
        gradient: Gradient,
        init: np.ndarray,
        steps: int,
    ) -> OptimizationResult:
        """Run ``steps`` gradient descent updates and record the full path."""

        return _run_optimizer(self, objective, gradient, init, steps)


class Momentum:
    """Heavy-ball momentum optimizer.

    The velocity follows ``v_t = beta * v_{t-1} + grad(theta_t)`` and the
    parameter update is ``theta_{t+1} = theta_t - lr * v_t``.
    """

    def __init__(self, lr: float, beta: float = 0.9) -> None:
        """Create a momentum optimizer."""

        if lr <= 0.0:
            raise ValueError("lr must be positive")
        if not 0.0 <= beta < 1.0:
            raise ValueError("beta must be in [0, 1)")
        self.lr = float(lr)
        self.beta = float(beta)
        self.velocity: np.ndarray | None = None

    def reset(self) -> None:
        """Clear the accumulated velocity."""

        self.velocity = None

    def step(self, point: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        """Return one momentum update."""

        point_array = np.asarray(point, dtype=float)
        gradient_array = np.asarray(gradient, dtype=float)
        if self.velocity is None:
            self.velocity = np.zeros_like(point_array, dtype=float)
        self.velocity = self.beta * self.velocity + gradient_array
        return point_array - self.lr * self.velocity

    def optimize(
        self,
        objective: Objective,
        gradient: Gradient,
        init: np.ndarray,
        steps: int,
    ) -> OptimizationResult:
        """Run ``steps`` momentum updates and record the full path."""

        self.reset()
        return _run_optimizer(self, objective, gradient, init, steps)


class Adam:
    """Adam optimizer combining momentum and RMSProp-style second moments."""

    def __init__(
        self,
        lr: float = 0.05,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
    ) -> None:
        """Create an Adam optimizer."""

        if lr <= 0.0:
            raise ValueError("lr must be positive")
        if not 0.0 <= beta1 < 1.0:
            raise ValueError("beta1 must be in [0, 1)")
        if not 0.0 <= beta2 < 1.0:
            raise ValueError("beta2 must be in [0, 1)")
        if eps <= 0.0:
            raise ValueError("eps must be positive")
        self.lr = float(lr)
        self.beta1 = float(beta1)
        self.beta2 = float(beta2)
        self.eps = float(eps)
        self.moment1: np.ndarray | None = None
        self.moment2: np.ndarray | None = None
        self.timestep = 0

    def reset(self) -> None:
        """Clear Adam moment estimates."""

        self.moment1 = None
        self.moment2 = None
        self.timestep = 0

    def step(self, point: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        """Return one Adam update with bias correction."""

        point_array = np.asarray(point, dtype=float)
        gradient_array = np.asarray(gradient, dtype=float)
        if self.moment1 is None or self.moment2 is None:
            self.moment1 = np.zeros_like(point_array, dtype=float)
            self.moment2 = np.zeros_like(point_array, dtype=float)
        self.timestep += 1
        self.moment1 = self.beta1 * self.moment1 + (1.0 - self.beta1) * gradient_array
        self.moment2 = self.beta2 * self.moment2 + (1.0 - self.beta2) * (
            gradient_array**2
        )
        corrected_m1 = self.moment1 / (1.0 - self.beta1**self.timestep)
        corrected_m2 = self.moment2 / (1.0 - self.beta2**self.timestep)
        return point_array - self.lr * corrected_m1 / (np.sqrt(corrected_m2) + self.eps)

    def optimize(
        self,
        objective: Objective,
        gradient: Gradient,
        init: np.ndarray,
        steps: int,
    ) -> OptimizationResult:
        """Run ``steps`` Adam updates and record the full path."""

        self.reset()
        return _run_optimizer(self, objective, gradient, init, steps)


def quadratic(point: np.ndarray) -> float:
    """Return ``f(x, y) = x^2 + y^2``."""

    point_array = np.asarray(point, dtype=float)
    return float(point_array[0] ** 2 + point_array[1] ** 2)


def quadratic_grad(point: np.ndarray) -> np.ndarray:
    """Return the gradient ``[2x, 2y]`` for ``x^2 + y^2``."""

    point_array = np.asarray(point, dtype=float)
    return np.array([2.0 * point_array[0], 2.0 * point_array[1]], dtype=float)


def elliptic_quadratic(point: np.ndarray) -> float:
    """Return ``f(x, y) = x^2 + 10y^2``."""

    point_array = np.asarray(point, dtype=float)
    return float(point_array[0] ** 2 + 10.0 * point_array[1] ** 2)


def elliptic_quadratic_grad(point: np.ndarray) -> np.ndarray:
    """Return the gradient ``[2x, 20y]`` for ``x^2 + 10y^2``."""

    point_array = np.asarray(point, dtype=float)
    return np.array([2.0 * point_array[0], 20.0 * point_array[1]], dtype=float)


def plot_convergence_paths(
    objective: Objective,
    paths: Mapping[str, np.ndarray],
    output_path: str | Path | None = None,
    xlim: tuple[float, float] = (-6.0, 6.0),
    ylim: tuple[float, float] = (-6.0, 6.0),
    title: str = "Optimization paths",
) -> plt.Figure:
    """Draw optimizer paths as dashed lines on an objective contour plot."""

    x_values = np.linspace(xlim[0], xlim[1], 220)
    y_values = np.linspace(ylim[0], ylim[1], 220)
    grid_x, grid_y = np.meshgrid(x_values, y_values)
    grid_z = np.zeros_like(grid_x)
    for row in range(grid_x.shape[0]):
        for col in range(grid_x.shape[1]):
            grid_z[row, col] = objective(np.array([grid_x[row, col], grid_y[row, col]]))

    figure, axis = plt.subplots(figsize=(7, 6))
    contours = axis.contour(grid_x, grid_y, grid_z, levels=18, cmap="viridis")
    axis.clabel(contours, inline=True, fontsize=8)
    for label, path in paths.items():
        path_array = np.asarray(path, dtype=float)
        axis.plot(
            path_array[:, 0],
            path_array[:, 1],
            linestyle="--",
            marker="o",
            markersize=2.5,
            linewidth=1.4,
            label=label,
        )
        axis.scatter(path_array[0, 0], path_array[0, 1], s=45)
        axis.scatter(path_array[-1, 0], path_array[-1, 1], s=55, marker="x")
    axis.set_title(title)
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.2)
    axis.legend()
    figure.tight_layout()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=160, bbox_inches="tight")
    return figure


def _run_optimizer(
    optimizer: VanillaGD | Momentum | Adam,
    objective: Objective,
    gradient: Gradient,
    init: np.ndarray,
    steps: int,
) -> OptimizationResult:
    """Shared optimization loop used by all optimizers."""

    if steps < 0:
        raise ValueError("steps must be non-negative")
    point = np.asarray(init, dtype=float)
    path = [point.copy()]
    values = [objective(point)]
    for _ in range(steps):
        point = optimizer.step(point, gradient(point))
        path.append(point.copy())
        values.append(objective(point))
    return OptimizationResult(path=np.asarray(path), values=np.asarray(values))
