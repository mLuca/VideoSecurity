import logging

import pytest

from app.config import Config


@pytest.fixture
def make_config(tmp_path):
    def _make_config(**overrides):
        kwargs = {"data_dir": tmp_path / "data", **overrides}
        config = Config(**kwargs)
        config.ensure_directories()
        return config

    return _make_config


@pytest.fixture
def logger():
    return logging.getLogger("test")
