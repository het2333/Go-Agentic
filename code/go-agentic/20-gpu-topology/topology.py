"""Bandwidth and collective-communication estimates for Chapter 20."""


def transfer_time_seconds(byte_count: int, bandwidth_gbps: float) -> float:
    """Return the ideal one-way transfer time at decimal Gbit/s."""
    if byte_count < 0:
        raise ValueError("byte_count cannot be negative")
    if bandwidth_gbps <= 0:
        raise ValueError("bandwidth_gbps must be positive")
    return byte_count * 8 / (bandwidth_gbps * 1_000_000_000)


def ring_all_reduce_bytes(payload_bytes: int, devices: int) -> float:
    """Return ideal traffic handled by each device in a ring all-reduce."""
    if payload_bytes < 0:
        raise ValueError("payload_bytes cannot be negative")
    if devices <= 0:
        raise ValueError("devices must be positive")
    return 2 * (devices - 1) / devices * payload_bytes
