import argparse
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Generic, Optional, TypeVar, cast

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import Config, DEFAULT_CONFIG_PATH
from app.live_stream import stream_hub
from app.logging_provider import setup_logging
from app.recorder import EventRecorder
from app.ring_buffer import RingBuffer
from app.trigger import extract_detections, find_trigger
from app.webapp.server import create_app

T = TypeVar("T")


class LazyGetter(Generic[T]):
    """Wraps a zero-arg factory and computes it at most once, on first `get()`."""

    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._value: Optional[T] = None
        self._done = False

    def get(self) -> T:
        if not self._done:
            self._value = self._factory()
            self._done = True
        return cast(T, self._value)


def has_display() -> bool:
    if os.name == "nt":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Muelltonnen Security: webcam detection loop and web UI.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path (absolute or relative) to a JSON configuration file. "
        f"Defaults to {DEFAULT_CONFIG_PATH}.",
    )
    return parser.parse_args()


def load_config(config_arg: str | None) -> Config:
    config_path = Path(config_arg).expanduser().resolve() if config_arg else DEFAULT_CONFIG_PATH
    try:
        return Config.load(config_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(message)s")
        logging.error("Failed to load configuration from %s: %s", config_path, exc)
        sys.exit(1)


def start_web_server(config: Config) -> None:
    app = create_app(config)
    app.run(host=config.web_host, port=config.web_port, threaded=True, use_reloader=False)


def main():
    args = parse_args()
    config = load_config(args.config)

    config.ensure_directories()
    logger = setup_logging(config)
    logger.info("Starting webcam detection.")

    model = YOLO(config.model_path)
    # First inference pays a one-time model setup cost (~1-2s); warm it up here with a "black image"
    # so it doesn't get mistaken for a sustained FPS drop once the paced loop starts.
    model(np.zeros((config.frame_height, config.frame_width, 3), dtype=np.uint8), verbose=False)

    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        logger.error("Could not open the webcam. Check that the USB camera is connected.")
        raise RuntimeError("Could not open the webcam. Check that the USB camera is connected.")
    else:
        logger.info("Webcam OK.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    target_fps = config.target_fps
    frame_interval = 1.0 / target_fps if target_fps > 0 else 0.0
    logger.info("Target processing FPS: %d (frame interval %.3fs).", target_fps, frame_interval)

    ring_buffer_size = max(1, round(target_fps * (config.pre_time + config.post_time)))
    ring_buffer = RingBuffer(ring_buffer_size)
    recorder = EventRecorder(config, logger, target_fps)

    web_thread = threading.Thread(target=start_web_server, args=(config,), daemon=True)
    web_thread.start()
    logger.info("Web UI listening on http://%s:%d", config.web_host, config.web_port)

    gui_enabled = has_display()
    if gui_enabled:
        logger.info("GUI display detected. Showing annotated webcam feed.")
    else:
        logger.info("No desktop display detected. Running headless; no GUI window will be shown.")

    try:
        was_behind_schedule = False
        while True:
            iteration_start = time.monotonic()
            try:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to read a frame from the webcam.")
                    break

                ring_buffer.append(frame)

                try:
                    results = model(frame, verbose=False)
                except Exception:
                    logger.exception("Model inference failed.")
                    continue

                # Computed at most once per iteration, only if someone actually needs it.
                annotated = LazyGetter(lambda: results[0].plot())

                try:
                    detections = extract_detections(results[0], config.detection_confidence)
                    trigger_event = find_trigger(detections, config.frame_width, config.frame_height, config)
                except Exception:
                    logger.exception("Error while evaluating trigger condition.")
                    trigger_event = None

                recorder.handle_frame(frame, trigger_event, annotated.get, ring_buffer.snapshot)

                if stream_hub.has_viewers:
                    stream_hub.publish_frame(annotated.get())

                if gui_enabled:
                    cv2.imshow("Muelltonnen Security", annotated.get())
                    cv2.waitKey(1)
            finally:
                # Pace the loop to target_fps regardless of how the iteration exited.
                if frame_interval > 0:
                    elapsed = time.monotonic() - iteration_start
                    remaining = frame_interval - elapsed
                    if remaining > 0:
                        time.sleep(remaining)
                        if was_behind_schedule:
                            was_behind_schedule = False
                            logger.info("Fps processed recovered to target_fps=%d again", target_fps)
                    elif remaining < 0:
                        if not was_behind_schedule:
                            achieved_fps = 1.0 / elapsed if elapsed > 0 else float("inf")
                            logger.warning(
                                "Falling behind target_fps=%d: iteration took %.3fs (~%.2f FPS achieved).",
                                target_fps,
                                elapsed,
                                achieved_fps,
                            )
                            was_behind_schedule = True
    except KeyboardInterrupt:
        logger.info("Shutdown requested (Ctrl+C).")
    finally:
        cap.release()
        if gui_enabled:
            cv2.destroyAllWindows()
        logger.info("Webcam loop stopped.")


if __name__ == "__main__":
    main()
