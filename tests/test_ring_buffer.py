import numpy as np
import pytest

from app.ring_buffer import RingBuffer


def frame(value):
    return np.full((2, 2, 3), value, dtype=np.uint8)


def test_maxlen_must_be_positive():
    with pytest.raises(ValueError):
        RingBuffer(0)


def test_append_and_snapshot_preserves_order():
    buffer = RingBuffer(maxlen=3)

    buffer.append(frame(1))
    buffer.append(frame(2))

    snapshot = buffer.snapshot()

    assert len(snapshot) == 2
    assert np.array_equal(snapshot[0], frame(1))
    assert np.array_equal(snapshot[1], frame(2))


def test_evicts_oldest_frame_beyond_maxlen():
    buffer = RingBuffer(maxlen=2)

    buffer.append(frame(1))
    buffer.append(frame(2))
    buffer.append(frame(3))

    snapshot = buffer.snapshot()

    assert len(snapshot) == 2
    assert np.array_equal(snapshot[0], frame(2))
    assert np.array_equal(snapshot[1], frame(3))


def test_snapshot_is_unaffected_by_later_appends():
    buffer = RingBuffer(maxlen=2)
    buffer.append(frame(1))

    snapshot = buffer.snapshot()
    buffer.append(frame(2))
    buffer.append(frame(3))  # evicts frame(1) from the live buffer

    assert len(snapshot) == 1
    assert np.array_equal(snapshot[0], frame(1))


def test_len_reflects_current_size():
    buffer = RingBuffer(maxlen=5)
    assert len(buffer) == 0

    buffer.append(frame(1))
    buffer.append(frame(2))

    assert len(buffer) == 2
