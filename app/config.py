"""Central configuration for the Muelltonnen Security application.

All values can be overridden via environment variables so the same code
works across different cameras/deployments without editing source.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value else default


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    # Model / camera
    model_path: str = str(BASE_DIR / "Model" / "Muell+Person_310726_yolo11n_ncnn_model")
    camera_index: int = _env_int("CAMERA_INDEX", 0)
    frame_width: int = _env_int("FRAME_WIDTH", 640)
    frame_height: int = _env_int("FRAME_HEIGHT", 480)
    default_fps: float = _env_float("CAMERA_FPS", 15.0)
    detection_confidence: float = _env_float("DETECTION_CONFIDENCE", 0.5)

    # Class names as defined in Model metadata.yaml
    person_class_name: str = "Person"
    trashbin_class_name: str = "German Trashbin"

    # Ring buffer / recording timing (seconds)
    pre_time: int = _env_int("PRE_TIME", 5)
    post_time: int = _env_int("POST_TIME", 10)

    # Trigger proximity thresholds ("lower and more to the right by at most
    # 60px, or 10% of the frame dimension - whichever is larger")
    trigger_max_pixels: int = _env_int("TRIGGER_MAX_PIXELS", 60)
    trigger_max_fraction: float = _env_float("TRIGGER_MAX_FRACTION", 0.1)

    # Storage
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    captures_dir_name: str = "captures"
    logs_dir_name: str = "logs"
    log_file_name: str = "app.log"
    video_extension: str = ".mp4"
    video_fourcc: str = "mp4v"

    # Web UI
    web_host: str = os.environ.get("WEBUI_HOST", "0.0.0.0")
    web_port: int = _env_int("WEBUI_PORT", 5000)
    web_password: str = os.environ.get("WEBUI_PASSWORD", "changeme")
    web_secret_key: str = os.environ.get("WEBUI_SECRET_KEY", secrets.token_hex(32))

    @property
    def captures_dir(self) -> Path:
        return self.data_dir / self.captures_dir_name

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / self.logs_dir_name

    @property
    def log_file(self) -> Path:
        return self.logs_dir / self.log_file_name

    def ensure_directories(self) -> None:
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


config = Config()
