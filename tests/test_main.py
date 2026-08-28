import json

import pytest

import main


def test_lazy_getter_calls_factory_at_most_once():
    calls = []

    def factory():
        calls.append(1)
        return "value"

    getter = main.LazyGetter(factory)

    assert getter.get() == "value"
    assert getter.get() == "value"
    assert len(calls) == 1


def test_lazy_getter_does_not_call_factory_until_get():
    calls = []
    main.LazyGetter(lambda: calls.append(1))

    assert calls == []


def test_has_display_true_on_windows(monkeypatch):
    monkeypatch.setattr(main.os, "name", "nt")

    assert main.has_display() is True


def test_has_display_uses_display_env_on_posix(monkeypatch):
    monkeypatch.setattr(main.os, "name", "posix")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert main.has_display() is False

    monkeypatch.setenv("DISPLAY", ":0")
    assert main.has_display() is True


def test_load_config_happy_path(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"camera_index": 3}), encoding="utf-8")

    config = main.load_config(str(path))

    assert config.camera_index == 3


def test_load_config_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit):
        main.load_config(str(tmp_path / "missing.json"))


def test_load_config_invalid_json_exits(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("not json", encoding="utf-8")

    with pytest.raises(SystemExit):
        main.load_config(str(path))
