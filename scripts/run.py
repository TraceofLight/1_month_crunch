"""Generate all figures and evidence files for the assignment."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.cbook as cbook
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.calculus import central_difference, plot_gradient_field
from src.linear_algebra import (
    compress_image_svd,
    plot_svd_comparison,
    plot_transformation,
    power_iteration,
    rotation_matrix,
    scaling_matrix,
    shear_matrix,
    unit_circle,
)
from src.optimizer import (
    Adam,
    Momentum,
    VanillaGD,
    elliptic_quadratic,
    elliptic_quadratic_grad,
    plot_convergence_paths,
    quadratic,
    quadratic_grad,
)
from src.probability import (
    bernoulli_pmf,
    cross_entropy,
    entropy,
    kl_divergence,
    plot_probability_distributions,
    softmax,
)


OUTPUT_DIR = ROOT / "outputs"
EVIDENCE_DIR = ROOT / "evidence"


def main() -> None:
    """Run every experiment and write figures plus text evidence."""

    np.random.seed(42)
    sns.set_theme(style="whitegrid")
    OUTPUT_DIR.mkdir(exist_ok=True)
    EVIDENCE_DIR.mkdir(exist_ok=True)

    evidence_lines: list[str] = []
    evidence_lines.extend(run_linear_algebra())
    evidence_lines.extend(run_calculus())
    evidence_lines.extend(run_backprop_check())
    evidence_lines.extend(run_optimization())
    evidence_lines.extend(run_probability())

    summary_path = EVIDENCE_DIR / "summary.txt"
    summary_path.write_text("\n".join(evidence_lines) + "\n", encoding="utf-8")
    print(f"wrote {summary_path.relative_to(ROOT)}")


def run_linear_algebra() -> list[str]:
    """Generate matrix-transform, Power Iteration, and SVD evidence."""

    lines = ["[linear_algebra]"]
    points = unit_circle(720)
    transforms = {
        "rotation": rotation_matrix(np.pi / 4.0),
        "scaling": scaling_matrix(2.0, 0.5),
        "shear": shear_matrix(1.0),
    }
    titles = {
        "rotation": "Rotation R(pi/4) on unit circle",
        "scaling": "Scaling S(2, 0.5) on unit circle",
        "shear": "Shear Sh(1.0) on unit circle",
    }

    for name, matrix in transforms.items():
        figure, stats = plot_transformation(
            matrix,
            titles[name],
            OUTPUT_DIR / f"{name}_transform.png",
            points=points,
        )
        plt.close(figure)
        lines.append(
            f"{name}: det={stats['determinant']:.6f}, "
            f"area_ratio={stats['area_ratio']:.6f}, "
            f"relative_error={stats['relative_error']:.8f}"
        )

    matrix = np.array([[4.0, 1.0], [1.0, 3.0]])
    power = power_iteration(matrix, tol=1e-10, max_iter=1_000, seed=42)
    eig_values, eig_vectors = np.linalg.eig(matrix)
    expected_index = int(np.argmax(eig_values.real))
    expected_value = float(eig_values[expected_index].real)
    expected_vector = eig_vectors[:, expected_index].real
    if np.dot(power.eigenvector, expected_vector) < 0:
        expected_vector = -expected_vector
    relative_error = abs(power.eigenvalue - expected_value) / abs(expected_value)
    lines.append(
        "power_iteration: "
        f"lambda={power.eigenvalue:.8f}, "
        f"numpy_lambda={expected_value:.8f}, "
        f"relative_error={relative_error:.8f}, "
        f"iterations={power.iterations}, converged={power.converged}"
    )
    lines.append(
        "power_iteration_vector: "
        f"computed={np.array2string(power.eigenvector, precision=6)}, "
        f"numpy={np.array2string(expected_vector, precision=6)}"
    )

    image = load_grayscale_sample(size=64)
    figure, svd_results = plot_svd_comparison(
        image, ks=(10, 50, 100), output_path=OUTPUT_DIR / "svd_compression.png"
    )
    plt.close(figure)
    for requested_k, result in zip((10, 50, 100), svd_results):
        lines.append(
            f"svd_k_{requested_k}: rank_used={result.rank_used}, "
            f"energy_ratio={result.energy_ratio:.8f}"
        )
    return lines


def run_calculus() -> list[str]:
    """Generate numerical-derivative and gradient-field evidence."""

    derivative = central_difference(lambda value: value**2, 3.0, h=1e-5)
    error = abs(derivative - 6.0)
    figure = plot_gradient_field(output_path=OUTPUT_DIR / "gradient_field.png")
    plt.close(figure)
    return [
        "[calculus]",
        f"central_difference_x2_at_3={derivative:.10f}",
        f"analytic_derivative=6.0000000000",
        f"absolute_error={error:.10f}",
    ]


def run_backprop_check() -> list[str]:
    """Run the fixed two-layer neural-network forward/backward example."""

    values = backprop_example()
    path = EVIDENCE_DIR / "backprop_numpy_check.txt"
    path.write_text(format_backprop_values(values), encoding="utf-8")
    return [
        "[backprop]",
        f"z1={np.array2string(values['z1'], precision=8)}",
        f"a1={np.array2string(values['a1'], precision=8)}",
        f"z2={values['z2']:.10f}",
        f"y_pred={values['y_pred']:.10f}",
        f"loss={values['loss']:.10f}",
        f"dL_dy_pred={values['dL_dy_pred']:.10f}",
        f"dL_dz2={values['dL_dz2']:.10f}",
        f"dL_dW2={np.array2string(values['dL_dW2'], precision=8)}",
        f"dL_da1={np.array2string(values['dL_da1'], precision=8)}",
        f"dL_dz1={np.array2string(values['dL_dz1'], precision=8)}",
        f"dL_dW1={np.array2string(values['dL_dW1'], precision=8)}",
    ]


def run_optimization() -> list[str]:
    """Generate optimizer path plots and convergence evidence."""

    init = np.array([5.0, 5.0])
    vanilla = VanillaGD(lr=0.1).optimize(quadratic, quadratic_grad, init, steps=100)
    figure = plot_convergence_paths(
        quadratic,
        {"Vanilla GD lr=0.1": vanilla.path},
        output_path=OUTPUT_DIR / "optimization_vanilla_quadratic.png",
        title="Vanilla GD on f(x,y)=x^2+y^2",
    )
    plt.close(figure)

    divergent = VanillaGD(lr=1.1).optimize(
        quadratic, quadratic_grad, np.array([1.0, 1.0]), steps=20
    )
    figure = plot_convergence_paths(
        quadratic,
        {"Vanilla GD lr=1.1": divergent.path},
        output_path=OUTPUT_DIR / "optimization_divergence_lr1_10.png",
        xlim=(-60.0, 60.0),
        ylim=(-60.0, 60.0),
        title="Divergent path example with lr=1.1",
    )
    plt.close(figure)

    momentum = Momentum(lr=0.1, beta=0.9).optimize(
        quadratic, quadratic_grad, init, steps=100
    )
    figure = plot_convergence_paths(
        quadratic,
        {
            "Vanilla GD lr=0.1": vanilla.path,
            "Momentum lr=0.1 beta=0.9": momentum.path,
        },
        output_path=OUTPUT_DIR / "optimization_momentum_compare.png",
        title="Vanilla GD vs Momentum on circular quadratic",
    )
    plt.close(figure)

    ellipse_vanilla = VanillaGD(lr=0.01).optimize(
        elliptic_quadratic, elliptic_quadratic_grad, init, steps=100
    )
    ellipse_momentum = Momentum(lr=0.01, beta=0.9).optimize(
        elliptic_quadratic, elliptic_quadratic_grad, init, steps=100
    )
    figure = plot_convergence_paths(
        elliptic_quadratic,
        {
            "Vanilla GD lr=0.01": ellipse_vanilla.path,
            "Momentum lr=0.01 beta=0.9": ellipse_momentum.path,
        },
        output_path=OUTPUT_DIR / "optimization_elliptic_compare.png",
        title="Vanilla GD vs Momentum on f(x,y)=x^2+10y^2",
    )
    plt.close(figure)

    adam = Adam(lr=0.12).optimize(elliptic_quadratic, elliptic_quadratic_grad, init, 100)
    figure = plot_convergence_paths(
        elliptic_quadratic,
        {
            "Vanilla GD lr=0.01": ellipse_vanilla.path,
            "Momentum lr=0.01 beta=0.9": ellipse_momentum.path,
            "Adam lr=0.12": adam.path,
        },
        output_path=OUTPUT_DIR / "optimization_adam_bonus.png",
        title="Bonus: Vanilla GD vs Momentum vs Adam",
    )
    plt.close(figure)

    return [
        "[optimization]",
        f"vanilla_lr_0_1_final={np.array2string(vanilla.final_point, precision=8)}",
        f"vanilla_lr_0_1_radius={np.linalg.norm(vanilla.final_point):.10f}",
        f"divergent_lr_1_1_start_radius={np.linalg.norm(divergent.path[0]):.10f}",
        f"divergent_lr_1_1_final_radius={np.linalg.norm(divergent.final_point):.10f}",
        f"momentum_lr_0_1_final={np.array2string(momentum.final_point, precision=8)}",
        f"ellipse_vanilla_final_value={ellipse_vanilla.final_value:.10f}",
        f"ellipse_momentum_final_value={ellipse_momentum.final_value:.10f}",
        f"ellipse_adam_final_value={adam.final_value:.10f}",
    ]


def run_probability() -> list[str]:
    """Generate probability distribution plots and loss-link evidence."""

    normal_figure, bernoulli_figure = plot_probability_distributions(
        normal_output_path=OUTPUT_DIR / "normal_pdfs.png",
        bernoulli_output_path=OUTPUT_DIR / "bernoulli_pmfs.png",
    )
    plt.close(normal_figure)
    plt.close(bernoulli_figure)

    probabilities = softmax(np.array([1.0, 2.0, 3.0]))
    probability_gap = abs(float(np.sum(probabilities)) - 1.0)
    p = np.array([0.25, 0.75])
    q = np.array([0.40, 0.60])
    return [
        "[probability]",
        f"normal_N_0_1_peak={np.max(plot_normal_values(0.0, 1.0)):.10f}",
        f"bernoulli_B_0_3={np.array2string(bernoulli_pmf(0.3), precision=8)}",
        f"bernoulli_B_0_7={np.array2string(bernoulli_pmf(0.7), precision=8)}",
        f"softmax={np.array2string(probabilities, precision=10)}",
        f"softmax_sum={np.sum(probabilities):.10f}",
        f"softmax_sum_gap={probability_gap:.12f}",
        f"entropy_bonus={entropy(p):.10f}",
        f"kl_divergence_bonus={kl_divergence(p, q):.10f}",
        f"cross_entropy_bonus={cross_entropy(p, q):.10f}",
    ]


def load_grayscale_sample(size: int = 64) -> np.ndarray:
    """Load a bundled public Matplotlib sample image and crop it to grayscale."""

    try:
        image = plt.imread(cbook.get_sample_data("grace_hopper.jpg"))
    except FileNotFoundError:
        grid = np.linspace(0.0, 1.0, size)
        x_grid, y_grid = np.meshgrid(grid, grid)
        return 0.6 * x_grid + 0.4 * np.sin(4.0 * np.pi * y_grid) ** 2

    image_array = np.asarray(image, dtype=float)
    if image_array.max() > 1.0:
        image_array = image_array / 255.0
    if image_array.ndim == 3:
        image_array = (
            0.299 * image_array[:, :, 0]
            + 0.587 * image_array[:, :, 1]
            + 0.114 * image_array[:, :, 2]
        )
    row_start = max((image_array.shape[0] - size) // 2, 0)
    col_start = max((image_array.shape[1] - size) // 2, 0)
    cropped = image_array[row_start : row_start + size, col_start : col_start + size]
    return cropped[:size, :size]


def sigmoid(values: np.ndarray | float) -> np.ndarray | float:
    """Return the sigmoid activation ``1 / (1 + exp(-z))``."""

    return 1.0 / (1.0 + np.exp(-values))


def backprop_example() -> dict[str, np.ndarray | float]:
    """Compute the fixed forward/backward example from the assignment."""

    x_value = np.array([1.0, 0.0])
    y_true = 1.0
    w1 = np.array([[0.1, 0.2], [0.3, 0.4]])
    b1 = np.array([0.0, 0.0])
    w2 = np.array([0.5, 0.6])
    b2 = 0.0

    z1 = w1 @ x_value + b1
    a1 = sigmoid(z1)
    z2 = float(w2 @ a1 + b2)
    y_pred = float(sigmoid(z2))
    loss = float(-(y_true * np.log(y_pred) + (1.0 - y_true) * np.log(1.0 - y_pred)))

    d_l_d_y_pred = float(-(y_true / y_pred) + ((1.0 - y_true) / (1.0 - y_pred)))
    d_l_d_z2 = float(y_pred - y_true)
    d_l_d_w2 = d_l_d_z2 * a1
    d_l_d_a1 = d_l_d_z2 * w2
    d_l_d_z1 = d_l_d_a1 * a1 * (1.0 - a1)
    d_l_d_w1 = np.outer(d_l_d_z1, x_value)

    return {
        "x": x_value,
        "y_true": y_true,
        "W1": w1,
        "b1": b1,
        "W2": w2,
        "b2": b2,
        "z1": z1,
        "a1": a1,
        "z2": z2,
        "y_pred": y_pred,
        "loss": loss,
        "dL_dy_pred": d_l_d_y_pred,
        "dL_dz2": d_l_d_z2,
        "dL_dW2": d_l_d_w2,
        "dL_da1": d_l_d_a1,
        "dL_dz1": d_l_d_z1,
        "dL_dW1": d_l_d_w1,
    }


def format_backprop_values(values: dict[str, np.ndarray | float]) -> str:
    """Format the backpropagation evidence as plain text."""

    lines = [
        "2-layer neural network NumPy verification",
        "x shape=(2,), W1 shape=(2,2), b1 shape=(2,), W2 shape=(2,), b2 scalar",
        f"z1 shape=(2,) {np.array2string(values['z1'], precision=10)}",
        f"a1 shape=(2,) {np.array2string(values['a1'], precision=10)}",
        f"z2 scalar {values['z2']:.10f}",
        f"y_pred scalar {values['y_pred']:.10f}",
        f"loss scalar {values['loss']:.10f}",
        f"dL/dy_pred scalar {values['dL_dy_pred']:.10f}",
        f"dL/dz2 scalar {values['dL_dz2']:.10f}",
        f"dL/dW2 shape=(2,) {np.array2string(values['dL_dW2'], precision=10)}",
        f"dL/da1 shape=(2,) {np.array2string(values['dL_da1'], precision=10)}",
        f"dL/dz1 shape=(2,) {np.array2string(values['dL_dz1'], precision=10)}",
        f"dL/dW1 shape=(2,2) {np.array2string(values['dL_dW1'], precision=10)}",
    ]
    return "\n".join(lines) + "\n"


def plot_normal_values(mean: float, std: float) -> np.ndarray:
    """Return normal-density values used for summary-only evidence."""

    from src.probability import normal_pdf

    x_values = np.linspace(-4.0, 5.0, 400)
    return normal_pdf(x_values, mean=mean, std=std)


if __name__ == "__main__":
    main()
