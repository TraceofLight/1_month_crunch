from rule_nlp.evaluation import compute_binary_metrics


def test_compute_binary_metrics_for_accuracy_precision_recall_f1():
    metrics = compute_binary_metrics(
        y_true=["positive", "negative", "positive", "negative"],
        y_pred=["positive", "positive", "positive", "negative"],
    )

    assert metrics["accuracy"] == 0.75
    assert metrics["precision"] == 0.6667
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 0.8
