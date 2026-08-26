"""Thread-safe hand-off point for the MJPEG live view.

The capture loop (main.py) pushes newly annotated frames in here whenever
`has_viewers` is true. The Flask stream endpoint (app/webapp/server.py) pulls
the latest JPEG-encoded frame per connected viewer, blocking efficiently
(via a Condition) instead of busy-polling.
"""
from __future__ import annotations

import threading
from typing import Optional

import cv2
import numpy as np


class StreamHub:
    def __init__(self, jpeg_quality: int = 80) -> None:
        self._jpeg_quality = jpeg_quality
        self._condition = threading.Condition()
        self._latest_jpeg: Optional[bytes] = None
        self._frame_id = 0
        self._viewer_count = 0

    @property
    def has_viewers(self) -> bool:
        with self._condition:
            return self._viewer_count > 0

    def add_viewer(self) -> None:
        with self._condition:
            self._viewer_count += 1

    def remove_viewer(self) -> None:
        with self._condition:
            self._viewer_count = max(0, self._viewer_count - 1)

    def publish_frame(self, annotated_frame: np.ndarray) -> None:
        ok, buffer = cv2.imencode(
            ".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality]
        )
        if not ok:
            return
        with self._condition:
            self._latest_jpeg = buffer.tobytes()
            self._frame_id += 1
            self._condition.notify_all()

    def next_frame(self, last_seen_id: int, timeout: float = 10.0) -> tuple[Optional[bytes], int]:
        """Block until a frame newer than `last_seen_id` is available.

        Returns (jpeg_bytes, frame_id); jpeg_bytes is None on timeout.
        """
        with self._condition:
            got = self._condition.wait_for(
                lambda: self._frame_id != last_seen_id, timeout=timeout
            )
            if not got:
                return None, last_seen_id
            return self._latest_jpeg, self._frame_id


stream_hub = StreamHub()
