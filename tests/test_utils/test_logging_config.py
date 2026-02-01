# tests/test_utils/test_logging_config.py
import logging
import os

import pytest
from utils.logging_config import create_default_logging_config, setup_logging


@pytest.fixture(autouse=True)
def cleanup_logging_file(tmp_path):
    # Ensure no logging.yaml exists before each test
    logging_file = tmp_path / "logging.yaml"
    if logging_file.exists():
        os.remove(logging_file)

    # Temporarily change the working directory to tmp_path
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_cwd)


def test_create_default_logging_config_creates_file(tmp_path):
    log_file_path = tmp_path / "logging.yaml"
    assert not log_file_path.exists()

    create_default_logging_config()
    assert log_file_path.exists()


def test_setup_logging_with_default_file(tmp_path):
    create_default_logging_config()  # Ensure default file exists

    # Configure a logger to capture messages
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid conflicts with other tests
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Use a StreamHandler for easier assertion
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    setup_logging(default_path="logging.yaml")

    # Test if logging works as expected
    logger.info("Test message from default config.")
    # Check if the log message appears (difficult to assert directly with file handler)
    # For a robust test, you'd inspect the log file content.

    # Check that root logger handlers are set up
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) >= 2  # console and file handler

    # Clean up the handler
    logger.removeHandler(handler)
    handler.close()


def test_setup_logging_without_file_uses_defaults(tmp_path, caplog):
    # Ensure no logging.yaml file
    assert not os.path.exists("logging.yaml")

    with caplog.at_level(logging.INFO):
        setup_logging(default_path="non_existent_logging.yaml")
        logging.info("Test message from basic config.")

    assert (
        "Failed to load logging configuration file. Using default configs"
        in caplog.text
    )
    assert "Test message from basic config." in caplog.text
