import json

import pytest

from app.config import BASE_DIR, Config


def test_load_flat_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"camera_index": 2, "target_fps": 15}), encoding="utf-8")

    config = Config.load(path)

    assert config.camera_index == 2
    assert config.target_fps == 15


def test_load_grouped_config_matches_flat(tmp_path):
    flat_path = tmp_path / "flat.json"
    flat_path.write_text(json.dumps({"camera_index": 2, "target_fps": 15}), encoding="utf-8")

    grouped_path = tmp_path / "grouped.json"
    grouped_path.write_text(
        json.dumps({"camera": {"camera_index": 2}, "performance": {"target_fps": 15}}),
        encoding="utf-8",
    )

    flat_config = Config.load(flat_path)
    grouped_config = Config.load(grouped_path)

    assert flat_config.camera_index == grouped_config.camera_index == 2
    assert flat_config.target_fps == grouped_config.target_fps == 15


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Config.load(tmp_path / "does-not-exist.json")


def test_load_invalid_json_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError):
        Config.load(path)


def test_load_non_object_json_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ValueError):
        Config.load(path)


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"camera_index": 1, "totally_made_up_field": "x"}), encoding="utf-8")

    config = Config.load(path)

    assert config.camera_index == 1
    assert not hasattr(config, "totally_made_up_field")


def test_relative_model_path_resolves_against_base_dir(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"model_path": "Model/foo"}), encoding="utf-8")

    config = Config.load(path)

    assert config.model_path == str(BASE_DIR / "Model" / "foo")


def test_absolute_data_dir_passes_through(tmp_path):
    absolute_dir = tmp_path / "somewhere"
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"data_dir": str(absolute_dir)}), encoding="utf-8")

    config = Config.load(path)

    assert config.data_dir == absolute_dir


def test_ensure_directories_creates_captures_and_logs(tmp_path):
    config = Config(data_dir=tmp_path / "data")

    config.ensure_directories()

    assert config.captures_dir.is_dir()
    assert config.logs_dir.is_dir()
