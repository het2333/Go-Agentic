"""Parallel-dimension, communication, and budget ledgers for Chapter 22."""

import math


def parallel_world_size(
    *,
    data: int = 1,
    tensor: int = 1,
    pipeline: int = 1,
    sequence: int = 1,
) -> int:
    """Return the device count implied by independent parallel dimensions."""
    dimensions = (data, tensor, pipeline, sequence)
    if any(value <= 0 for value in dimensions):
        raise ValueError("parallel dimensions must be positive")
    return math.prod(dimensions)


def sequence_shard_length(sequence_length: int, sequence_parallel: int) -> int:
    """Return the padded per-rank sequence length."""
    if sequence_length <= 0:
        raise ValueError("sequence_length must be positive")
    if sequence_parallel <= 0:
        raise ValueError("sequence_parallel must be positive")
    return math.ceil(sequence_length / sequence_parallel)


def data_parallel_sync_bytes(gradient_bytes: int, data_parallel: int) -> float:
    """Return ideal per-device ring all-reduce traffic for gradient sync."""
    if gradient_bytes < 0:
        raise ValueError("gradient_bytes cannot be negative")
    if data_parallel <= 0:
        raise ValueError("data_parallel must be positive")
    return 2 * (data_parallel - 1) / data_parallel * gradient_bytes


def training_budget(
    devices: int,
    runtime_hours: float,
    hourly_cost_per_device: float,
) -> dict[str, float]:
    """Return device-hours and a simple accelerator-only cost estimate."""
    if devices <= 0:
        raise ValueError("devices must be positive")
    if runtime_hours < 0:
        raise ValueError("runtime_hours cannot be negative")
    if hourly_cost_per_device < 0:
        raise ValueError("hourly_cost_per_device cannot be negative")
    device_hours = devices * runtime_hours
    return {
        "device_hours": device_hours,
        "estimated_cost": device_hours * hourly_cost_per_device,
    }
