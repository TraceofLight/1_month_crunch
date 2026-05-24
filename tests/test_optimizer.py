import numpy as np

from src.optimizer import Momentum, VanillaGD, quadratic, quadratic_grad


def test_vanilla_gd_reaches_origin_neighborhood_after_100_steps():
    optimizer = VanillaGD(lr=0.1)
    result = optimizer.optimize(quadratic, quadratic_grad, init=np.array([5.0, 5.0]), steps=100)

    assert np.linalg.norm(result.final_point) <= 0.1
    assert result.path.shape == (101, 2)


def test_large_learning_rate_example_diverges_for_quadratic():
    optimizer = VanillaGD(lr=1.1)
    result = optimizer.optimize(quadratic, quadratic_grad, init=np.array([1.0, 1.0]), steps=20)

    assert np.linalg.norm(result.final_point) > np.linalg.norm(result.path[0])


def test_momentum_improves_elliptic_quadratic_with_conservative_lr():
    def elliptic(point):
        return point[0] ** 2 + 10.0 * point[1] ** 2

    def elliptic_grad(point):
        return np.array([2.0 * point[0], 20.0 * point[1]])

    init = np.array([5.0, 5.0])
    vanilla = VanillaGD(lr=0.01).optimize(elliptic, elliptic_grad, init=init, steps=100)
    momentum = Momentum(lr=0.01, beta=0.9).optimize(elliptic, elliptic_grad, init=init, steps=100)

    assert elliptic(momentum.final_point) < elliptic(vanilla.final_point)
