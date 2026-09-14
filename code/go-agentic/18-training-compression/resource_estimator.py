"""Transparent memory and compression estimates for Chapter 18."""


def estimate_adamw_memory(
    parameter_count: int,
    *,
    parameter_bytes: int = 2,
    gradient_bytes: int = 2,
    master_weight_bytes: int = 4,
    moment_bytes: int = 4,
    activation_bytes: int = 0,
) -> dict[str, int]:
    """Estimate unsharded training memory for mixed-precision AdamW."""
    if parameter_count <= 0:
        raise ValueError("parameter_count must be positive")
    byte_widths = [parameter_bytes, gradient_bytes, master_weight_bytes, moment_bytes]
    if any(value < 0 for value in byte_widths) or activation_bytes < 0:
        raise ValueError("byte sizes cannot be negative")

    result = {
        "parameters": parameter_count * parameter_bytes,
        "gradients": parameter_count * gradient_bytes,
        "master_weights": parameter_count * master_weight_bytes,
        "moments": parameter_count * moment_bytes * 2,
        "activations": activation_bytes,
    }
    result["total"] = sum(result.values())
    return result


def compression_ratio(original_bits: int, target_bits: int, *, sparsity: float = 0.0) -> float:
    """Return the ideal storage reduction from lower precision and sparsity."""
    if original_bits <= 0 or target_bits <= 0:
        raise ValueError("bit widths must be positive")
    if not 0.0 <= sparsity < 1.0:
        raise ValueError("sparsity must be in [0, 1)")
    return original_bits / (target_bits * (1.0 - sparsity))
