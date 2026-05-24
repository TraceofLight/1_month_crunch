"""Probability utilities used by the loss-function notebook and script."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def normal_pdf(x_values: np.ndarray, mean: float, std: float) -> np.ndarray:
    """Return the normal PDF ``N(mean, std^2)`` at ``x_values``."""

    if std <= 0.0:
        raise ValueError("std must be positive")
    x_array = np.asarray(x_values, dtype=float)
    coefficient = 1.0 / (std * np.sqrt(2.0 * np.pi))
    exponent = -((x_array - mean) ** 2) / (2.0 * std**2)
    return coefficient * np.exp(exponent)


def bernoulli_pmf(probability: float) -> np.ndarray:
    """Return ``P(X=0)`` and ``P(X=1)`` for a Bernoulli distribution."""

    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    return np.array([1.0 - probability, probability], dtype=float)


def softmax(logits: np.ndarray) -> np.ndarray:
    """Return a numerically stable softmax probability vector."""

    logits_array = np.asarray(logits, dtype=float)
    shifted = logits_array - np.max(logits_array)
    exp_values = np.exp(shifted)
    return exp_values / np.sum(exp_values)


def entropy(probabilities: np.ndarray, eps: float = 1e-12) -> float:
    """Return Shannon entropy ``H(P) = -sum p log p``."""

    probs = _validate_probabilities(probabilities)
    return float(-np.sum(probs * np.log(probs + eps)))


def kl_divergence(
    p_distribution: np.ndarray,
    q_distribution: np.ndarray,
    eps: float = 1e-12,
) -> float:
    """Return ``KL(P || Q) = sum p log(p / q)``."""

    p_probs = _validate_probabilities(p_distribution)
    q_probs = _validate_probabilities(q_distribution)
    if p_probs.shape != q_probs.shape:
        raise ValueError("distributions must have the same shape")
    return float(np.sum(p_probs * np.log((p_probs + eps) / (q_probs + eps))))


def cross_entropy(
    p_distribution: np.ndarray,
    q_distribution: np.ndarray,
    eps: float = 1e-12,
) -> float:
    """Return cross-entropy ``H(P, Q) = -sum p log q``."""

    p_probs = _validate_probabilities(p_distribution)
    q_probs = _validate_probabilities(q_distribution)
    if p_probs.shape != q_probs.shape:
        raise ValueError("distributions must have the same shape")
    return float(-np.sum(p_probs * np.log(q_probs + eps)))


def plot_probability_distributions(
    normal_output_path: str | Path | None = None,
    bernoulli_output_path: str | Path | None = None,
) -> tuple[plt.Figure, plt.Figure]:
    """Plot required normal PDFs and Bernoulli PMFs."""

    x_values = np.linspace(-4.0, 5.0, 400)
    normal_figure, normal_axis = plt.subplots(figsize=(7, 4.5))
    normal_axis.plot(x_values, normal_pdf(x_values, 0.0, 1.0), label="N(0, 1)")
    normal_axis.plot(x_values, normal_pdf(x_values, 2.0, 0.5), label="N(2, 0.5)")
    normal_axis.set_title("Normal distribution PDFs")
    normal_axis.set_xlabel("x")
    normal_axis.set_ylabel("density")
    normal_axis.grid(True, alpha=0.25)
    normal_axis.legend()
    normal_figure.tight_layout()

    bernoulli_figure, bernoulli_axis = plt.subplots(figsize=(6, 4.5))
    x_positions = np.array([0, 1])
    width = 0.34
    bernoulli_axis.bar(
        x_positions - width / 2,
        bernoulli_pmf(0.3),
        width=width,
        label="B(0.3)",
    )
    bernoulli_axis.bar(
        x_positions + width / 2,
        bernoulli_pmf(0.7),
        width=width,
        label="B(0.7)",
    )
    bernoulli_axis.set_xticks(x_positions)
    bernoulli_axis.set_xlabel("outcome")
    bernoulli_axis.set_ylabel("probability")
    bernoulli_axis.set_title("Bernoulli PMFs")
    bernoulli_axis.set_ylim(0.0, 1.0)
    bernoulli_axis.grid(True, axis="y", alpha=0.25)
    bernoulli_axis.legend()
    bernoulli_figure.tight_layout()

    if normal_output_path is not None:
        _save_figure(normal_figure, normal_output_path)
    if bernoulli_output_path is not None:
        _save_figure(bernoulli_figure, bernoulli_output_path)
    return normal_figure, bernoulli_figure


def _validate_probabilities(probabilities: np.ndarray) -> np.ndarray:
    """Validate that an array is a probability vector."""

    probs = np.asarray(probabilities, dtype=float)
    if probs.ndim != 1:
        raise ValueError("probabilities must be a 1D vector")
    if np.any(probs < 0.0):
        raise ValueError("probabilities must be non-negative")
    if not np.isclose(np.sum(probs), 1.0):
        raise ValueError("probabilities must sum to 1")
    return probs


def _save_figure(figure: plt.Figure, output_path: str | Path) -> None:
    """Create the parent directory and save a Matplotlib figure."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160, bbox_inches="tight")
