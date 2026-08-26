import argparse
import logging
import os
import sys
import threading
from pathlib import Path

import cv2
from ultralytics import YOLO

from app.config import Config, DEFAULT_CONFIG_PATH
from app.live_stream import stream_hub
from app.logging_provider import setup_logging
from app.recorder import EventRecorder
from app.ring_buffer import RingBuffer
from app.trigger import extract_detections, find_trigger
from app.webapp.server import create_app


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

    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        logger.error("Could not open the webcam. Check that the USB camera is connected.")
        raise RuntimeError("Could not open the webcam. Check that the USB camera is connected.")
    else:
        logger.info("Webcam OK.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = config.default_fps
    logger.info("Camera FPS: %.2f", fps)

    ring_buffer_size = max(1, round(fps * (config.pre_time + config.post_time)))
    ring_buffer = RingBuffer(ring_buffer_size)
    recorder = EventRecorder(config, logger, fps)

    web_thread = threading.Thread(target=start_web_server, args=(config,), daemon=True)
    web_thread.start()
    logger.info("Web UI listening on http://%s:%d", config.web_host, config.web_port)

    gui_enabled = has_display()
    if gui_enabled:
        logger.info("GUI display detected. Showing annotated webcam feed.")
    else:
        logger.info("No desktop display detected. Running headless; no GUI window will be shown.")

    try:
        while True:
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

            # Only pay the annotation-drawing cost when it's actually needed.
            needs_annotated_frame = gui_enabled or stream_hub.has_viewers

            if recorder.is_recording:
                recorder.feed_post_frame(frame)
                annotated_frame = results[0].plot() if needs_annotated_frame else None
            else:
                annotated_frame = None
                try:
                    detections = extract_detections(results[0], config.detection_confidence)
                    trigger_event = find_trigger(detections, config.frame_width, config.frame_height, config)
                    if trigger_event is not None:
                        annotated_frame = results[0].plot()
                        recorder.maybe_trigger(trigger_event, annotated_frame, ring_buffer.snapshot())
                except Exception:
                    logger.exception("Error while evaluating trigger condition.")

                if needs_annotated_frame and annotated_frame is None:
                    annotated_frame = results[0].plot()

            if annotated_frame is not None and stream_hub.has_viewers:
                stream_hub.publish_frame(annotated_frame)

            if gui_enabled:
                cv2.imshow("Muelltonnen Security", annotated_frame)
                cv2.waitKey(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested (Ctrl+C).")
    finally:
        cap.release()
        if gui_enabled:
            cv2.destroyAllWindows()
        logger.info("Webcam loop stopped.")


if __name__ == "__main__":
    main()
