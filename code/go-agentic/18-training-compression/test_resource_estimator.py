import pytest

from resource_estimator import compression_ratio, estimate_adamw_memory


def test_adamw_memory_exposes_each_component():
    result = estimate_adamw_memory(100, activation_bytes=500)
    assert result == {
        "parameters": 200,
        "gradients": 200,
        "master_weights": 400,
        "moments": 800,
        "activations": 500,
        "total": 2100,
    }


def test_compression_ratio_combines_precision_and_sparsity():
    assert compression_ratio(16, 4, sparsity=0.5) == pytest.approx(8.0)


@pytest.mark.parametrize("parameter_count", [0, -1])
def test_adamw_memory_rejects_non_positive_parameter_count(parameter_count):
    with pytest.raises(ValueError, match="positive"):
        estimate_adamw_memory(parameter_count)
