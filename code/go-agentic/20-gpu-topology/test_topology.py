import pytest

from topology import ring_all_reduce_bytes, transfer_time_seconds


def test_transfer_time_converts_gigabits_to_bytes():
    assert transfer_time_seconds(1_000_000_000, 8.0) == pytest.approx(1.0)


def test_ring_all_reduce_reports_per_device_traffic():
    assert ring_all_reduce_bytes(1_000, 4) == pytest.approx(1_500.0)


@pytest.mark.parametrize("devices", [0, -2])
def test_all_reduce_rejects_invalid_device_count(devices):
    with pytest.raises(ValueError, match="devices"):
        ring_all_reduce_bytes(1_000, devices)
