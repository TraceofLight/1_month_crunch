import numpy as np

from src.calculus import central_difference, numerical_gradient


def test_central_difference_matches_analytic_derivative_for_square():
    derivative = central_difference(lambda x: x**2, 3.0, h=1e-5)

    assert abs(derivative - 6.0) <= 1e-4


def test_numerical_gradient_matches_quadratic_gradient():
    point = np.array([3.0, 4.0])
    gradient = numerical_gradient(lambda values: values[0] ** 2 + values[1] ** 2, point)

    np.testing.assert_allclose(gradient, np.array([6.0, 8.0]), atol=1e-4)
