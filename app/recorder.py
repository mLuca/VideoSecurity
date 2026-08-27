"""Handles persisting the trigger frame and the pre/post event video clip."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from app.config import Config
from app.trigger import TriggerEvent


class EventRecorder:
    """State machine: idle -> recording_post -> idle.

    While idle, a new trigger immediately saves the annotated trigger frame
    and starts collecting `post_time` seconds worth of subsequent raw frames.
    While recording, new triggers are ignored so a single event is captured.
    """

    def __init__(self, config: Config, logger: logging.Logger, fps: float) -> None:
        self._config = config
        self._logger = logger
        self._fps = fps
        self._post_target_frames = max(1, round(config.post_time * fps))

        self._recording = False
        self._event_dir: Optional[Path] = None
        self._pre_frames: List[np.ndarray] = []
        self._post_frames: List[np.ndarray] = []

    @property
    def is_recording(self) -> bool:
        return self._recording

    def maybe_trigger(
        self,
        trigger_event: TriggerEvent,
        annotated_frame: np.ndarray,
        pre_frames: List[np.ndarray],
    ) -> None:
        if self._recording:
            return

        timestamp = datetime.now()
        event_name = timestamp.strftime("%Y-%m-%d-%H-%M-%S")
        self._event_dir = self._config.captures_dir / event_name
        self._event_dir.mkdir(parents=True, exist_ok=True)
        self._pre_frames = pre_frames
        self._post_frames = []
        self._recording = True

        self._save_trigger_frame(annotated_frame)

        self._logger.info(
            "Recording triggered: person center=(%.1f, %.1f) trashbin center=(%.1f, %.1f) "
            "dx=%.1f dy=%.1f thresholds=(%.1f, %.1f)",
            *trigger_event.person.center,
            *trigger_event.trashbin.center,
            trigger_event.dx,
            trigger_event.dy,
            trigger_event.threshold_x,
            trigger_event.threshold_y,
        )

    def feed_post_frame(self, frame: np.ndarray) -> None:
        if not self._recording:
            return

        self._post_frames.append(frame.copy())
        if len(self._post_frames) >= self._post_target_frames:
            self._finalize_video()
            self._recording = False
            self._event_dir = None
            self._pre_frames = []
            self._post_frames = []

    def _save_trigger_frame(self, annotated_frame: np.ndarray) -> None:
        if self._event_dir is None:
            return
        path = self._event_dir / "trigger.jpeg"
        try:
            cv2.imwrite(str(path), annotated_frame)
            self._logger.info("Saved trigger frame to %s", path)
        except Exception:
            self._logger.exception("Failed to save trigger frame to %s", path)

    def _finalize_video(self) -> None:
        frames = self._pre_frames + self._post_frames
        if not frames:
            self._logger.error("No frames collected for event %s; skipping video", self._event_dir)
            return

        if self._event_dir is None:
            return
        path = self._event_dir / "video.mp4"
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*self._config.video_fourcc)
        writer = cv2.VideoWriter(str(path), fourcc, self._fps, (width, height))

        try:
            if not writer.isOpened():
                raise RuntimeError(f"VideoWriter failed to open output file {path}")
            for frame in frames:
                writer.write(frame)
            self._logger.info("Saved event video to %s (%d frames)", path, len(frames))
        except Exception:
            self._logger.exception("Failed to write event video to %s", path)
        finally:
            writer.release()
