from logging.handlers import RotatingFileHandler

from app.logging_provider import get_logger, setup_logging


def test_setup_logging_creates_log_file_and_handlers(make_config):
    config = make_config()

    logger = setup_logging(config)

    assert config.log_file.exists()
    assert len(logger.handlers) == 2
    assert any(isinstance(h, RotatingFileHandler) for h in logger.handlers)


def test_setup_logging_does_not_duplicate_handlers_on_repeat_calls(make_config):
    config = make_config()

    setup_logging(config)
    setup_logging(config)

    logger = get_logger()
    assert len(logger.handlers) == 2


def test_get_logger_returns_same_named_logger(make_config):
    config = make_config()
    logger = setup_logging(config)

    assert get_logger() is logger
