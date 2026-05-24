import numpy as np

from src.probability import bernoulli_pmf, normal_pdf, softmax


def test_softmax_outputs_probability_vector():
    probabilities = softmax(np.array([1.0, 2.0, 3.0]))

    assert np.all(probabilities > 0.0)
    assert abs(np.sum(probabilities) - 1.0) <= 1e-6


def test_normal_pdf_is_symmetric_around_mean():
    left = normal_pdf(np.array([-1.0]), mean=0.0, std=1.0)[0]
    right = normal_pdf(np.array([1.0]), mean=0.0, std=1.0)[0]

    assert np.isclose(left, right)


def test_bernoulli_pmf_returns_failure_and_success_probabilities():
    pmf = bernoulli_pmf(0.7)

    np.testing.assert_allclose(pmf, np.array([0.3, 0.7]))
