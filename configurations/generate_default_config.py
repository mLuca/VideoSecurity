"""Generates configurations/default_config.json from Config's dataclass defaults.

Re-run this whenever Config's fields/defaults change, or to get a fresh
default_config.json with a newly generated web_secret_key:

    uv run python configurations/generate_default_config.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR, DEFAULT_CONFIG_PATH, Config  # noqa: E402

# Field groupings mirror the section comments in app/config.py, purely for
# readability of the generated JSON file.
_SECTIONS: dict[str, list[str]] = {
    "model_camera": [
        "model_path",
        "camera_index",
        "frame_width",
        "frame_height",
        "default_fps",
        "detection_confidence",
    ],
    "class_names": ["person_class_name", "trashbin_class_name"],
    "ring_buffer": ["pre_time", "post_time"],
    "trigger": ["trigger_max_pixels", "trigger_max_fraction"],
    "storage": [
        "data_dir",
        "captures_dir_name",
        "logs_dir_name",
        "log_file_name",
        "video_extension",
        "video_fourcc",
    ],
    "web_ui": ["web_host", "web_port", "web_password", "web_secret_key"],
}


def _to_json_value(name: str, value: object) -> object:
    if name in ("model_path", "data_dir"):
        # Store paths relative to the project root so the file stays portable.
        return str(Path(value).resolve().relative_to(BASE_DIR)).replace("\\", "/")
    return value


def build_default_config() -> dict[str, dict[str, object]]:
    defaults = Config()
    return {
        section: {name: _to_json_value(name, getattr(defaults, name)) for name in names}
        for section, names in _SECTIONS.items()
    }


def generate(path: Path = DEFAULT_CONFIG_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(build_default_config(), fh, indent=2)
        fh.write("\n")
    return path


if __name__ == "__main__":
    output_path = generate()
    print(f"Wrote {output_path}")
