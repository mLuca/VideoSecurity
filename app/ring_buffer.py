"""Thread-safe fixed-size buffer of raw camera frames."""
from __future__ import annotations

import threading
from collections import deque
from typing import List

import numpy as np


class RingBuffer:
    def __init__(self, maxlen: int) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be a positive integer")
        self._buffer: deque[np.ndarray] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def append(self, frame: np.ndarray) -> None:
        with self._lock:
            self._buffer.append(frame.copy())

    def snapshot(self) -> List[np.ndarray]:
        """Return a copy of the buffer contents in chronological order."""
        with self._lock:
            return list(self._buffer)

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)
