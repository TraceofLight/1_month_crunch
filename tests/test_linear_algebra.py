import numpy as np

from src.linear_algebra import (
    compress_image_svd,
    power_iteration,
    rotation_matrix,
    scaling_matrix,
    shear_matrix,
    transform_area_comparison,
    unit_circle,
)


def test_transform_area_ratio_matches_absolute_determinant():
    points = unit_circle(num_points=720)

    for matrix in (
        rotation_matrix(np.pi / 4),
        scaling_matrix(2.0, 0.5),
        shear_matrix(1.25),
    ):
        stats = transform_area_comparison(matrix, points)
        assert stats["relative_error"] <= 0.01


def test_scaling_matrix_maps_unit_circle_to_expected_ellipse_bounds():
    points = unit_circle(num_points=720)
    transformed = points @ scaling_matrix(2.0, 0.5).T

    assert np.isclose(np.max(np.abs(transformed[:, 0])), 2.0, atol=1e-4)
    assert np.isclose(np.max(np.abs(transformed[:, 1])), 0.5, atol=1e-4)


def test_power_iteration_matches_numpy_dominant_eigenvalue():
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]])

    result = power_iteration(matrix, tol=1e-10, max_iter=1_000, seed=42)
    expected = np.max(np.linalg.eigvals(matrix).real)
    relative_error = abs(result.eigenvalue - expected) / abs(expected)

    assert relative_error <= 0.05
    assert np.isclose(np.linalg.norm(result.eigenvector), 1.0)
    assert result.iterations < 1_000


def test_svd_compression_preserves_shape_and_full_rank_reconstructs_matrix():
    image = np.arange(64, dtype=float).reshape(8, 8)

    compressed_low = compress_image_svd(image, k=3)
    compressed_full = compress_image_svd(image, k=100)

    assert compressed_low.reconstructed.shape == image.shape
    assert compressed_low.rank_used == 3
    assert compressed_full.rank_used == 8
    np.testing.assert_allclose(compressed_full.reconstructed, image, atol=1e-10)
