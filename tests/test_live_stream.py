import threading
import time

import numpy as np

from app.live_stream import StreamHub


def frame():
    return np.zeros((4, 4, 3), dtype=np.uint8)


def test_no_viewers_by_default():
    hub = StreamHub()
    assert hub.has_viewers is False


def test_add_and_remove_viewer_counts():
    hub = StreamHub()

    hub.add_viewer()
    assert hub.has_viewers is True

    hub.add_viewer()
    hub.remove_viewer()
    assert hub.has_viewers is True  # one viewer left

    hub.remove_viewer()
    assert hub.has_viewers is False


def test_remove_viewer_floors_at_zero():
    hub = StreamHub()

    hub.remove_viewer()  # no-op, must not go negative

    hub.add_viewer()
    hub.remove_viewer()
    hub.remove_viewer()
    assert hub.has_viewers is False


def test_next_frame_times_out_when_nothing_published():
    hub = StreamHub()

    jpeg, frame_id = hub.next_frame(last_seen_id=0, timeout=0.05)

    assert jpeg is None
    assert frame_id == 0


def test_publish_frame_wakes_up_waiting_consumer():
    hub = StreamHub()
    result = {}

    def consume():
        result["jpeg"], result["frame_id"] = hub.next_frame(last_seen_id=0, timeout=5.0)

    consumer = threading.Thread(target=consume)
    consumer.start()
    time.sleep(0.05)  # give the consumer a chance to start waiting
    hub.publish_frame(frame())
    consumer.join(timeout=5.0)

    assert result["jpeg"] is not None
    assert result["frame_id"] == 1
