"""ZeRO and FSDP memory estimates for Chapter 22."""


def zero_memory_per_device(
    parameter_count: int,
    devices: int,
    *,
    stage: int,
    parameter_bytes: int = 2,
    gradient_bytes: int = 2,
    master_weight_bytes: int = 4,
    moment_bytes: int = 4,
) -> dict[str, int]:
    """Estimate per-device model-state bytes for ZeRO stages 0 through 3."""
    if parameter_count <= 0:
        raise ValueError("parameter_count must be positive")
    if devices <= 0:
        raise ValueError("devices must be positive")
    if stage not in {0, 1, 2, 3}:
        raise ValueError("stage must be 0, 1, 2, or 3")

    shards = {
        "parameters": devices if stage >= 3 else 1,
        "gradients": devices if stage >= 2 else 1,
        "master_weights": devices if stage >= 1 else 1,
        "moments": devices if stage >= 1 else 1,
    }
    result = {
        "parameters": parameter_count * parameter_bytes // shards["parameters"],
        "gradients": parameter_count * gradient_bytes // shards["gradients"],
        "master_weights": parameter_count * master_weight_bytes // shards["master_weights"],
        "moments": parameter_count * moment_bytes * 2 // shards["moments"],
    }
    result["total"] = sum(result.values())
    return result


def fsdp_shard_bytes(full_state_bytes: int, devices: int) -> int:
    """Return ideal per-device bytes under full sharding."""
    if full_state_bytes < 0:
        raise ValueError("full_state_bytes cannot be negative")
    if devices <= 0:
        raise ValueError("devices must be positive")
    return (full_state_bytes + devices - 1) // devices
