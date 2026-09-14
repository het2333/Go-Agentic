"""Deterministic performance and cost ledgers for Chapter 20."""


def _positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def roofline_ceiling(
    peak_compute_flops: float,
    memory_bandwidth_bytes_per_second: float,
    arithmetic_intensity_flops_per_byte: float,
) -> float:
    """Return the attainable FLOP/s ceiling from the Roofline model."""
    _positive("peak_compute_flops", peak_compute_flops)
    _positive("memory_bandwidth_bytes_per_second", memory_bandwidth_bytes_per_second)
    _positive("arithmetic_intensity_flops_per_byte", arithmetic_intensity_flops_per_byte)
    memory_ceiling = memory_bandwidth_bytes_per_second * arithmetic_intensity_flops_per_byte
    return min(peak_compute_flops, memory_ceiling)


def model_flops_utilization(
    achieved_flops: float,
    elapsed_seconds: float,
    peak_flops_per_second: float,
) -> float:
    """Return achieved model work divided by theoretical peak work."""
    if achieved_flops < 0:
        raise ValueError("achieved_flops cannot be negative")
    _positive("elapsed_seconds", elapsed_seconds)
    _positive("peak_flops_per_second", peak_flops_per_second)
    return achieved_flops / (elapsed_seconds * peak_flops_per_second)


def classify_bottleneck(
    peak_compute_flops: float,
    memory_bandwidth_bytes_per_second: float,
    arithmetic_intensity_flops_per_byte: float,
) -> str:
    """Classify a workload against the Roofline ridge point."""
    _positive("peak_compute_flops", peak_compute_flops)
    _positive("memory_bandwidth_bytes_per_second", memory_bandwidth_bytes_per_second)
    if arithmetic_intensity_flops_per_byte < 0:
        raise ValueError("arithmetic_intensity_flops_per_byte cannot be negative")
    ridge_point = peak_compute_flops / memory_bandwidth_bytes_per_second
    return "memory-bound" if arithmetic_intensity_flops_per_byte < ridge_point else "compute-bound"


def estimate_accelerator_cost(
    devices: int,
    runtime_hours: float,
    hourly_cost_per_device: float,
) -> float:
    """Return an infrastructure-only accelerator cost estimate."""
    _positive("devices", devices)
    if runtime_hours < 0:
        raise ValueError("runtime_hours cannot be negative")
    if hourly_cost_per_device < 0:
        raise ValueError("hourly_cost_per_device cannot be negative")
    return devices * runtime_hours * hourly_cost_per_device
