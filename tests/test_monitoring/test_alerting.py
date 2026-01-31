# tests/test_monitoring/test_alerting.py
import os

import pytest
from src.monitoring.alerting import Alerting


@pytest.fixture
def alerting(test_config, monkeypatch):
    # Mock environment variables for testing
    monkeypatch.setenv("ALERT_TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("ALERT_TELEGRAM_CHAT_ID", "test_chat_id")
    monkeypatch.setenv("ALERT_EMAIL_SENDER", "test@example.com")
    monkeypatch.setenv("ALERT_EMAIL_RECIPIENT", "recipient@example.com")
    return Alerting(test_config)


def test_send_urgent_alert(alerting, mocker):
    mock_send_telegram = mocker.patch.object(alerting, "_send_telegram_message")
    mock_send_email = mocker.patch.object(alerting, "_send_email")

    alerting.send_urgent_alert("Critical issue detected!")

    mock_send_telegram.assert_called_once_with("🚨 URGENT: Critical issue detected!")
    mock_send_email.assert_called_once_with(
        "URGENT ALERT: Strategy Optimizer", "Critical issue detected!"
    )


def test_send_daily_summary(alerting, mocker):
    mock_send_email = mocker.patch.object(alerting, "_send_email")

    alerting.send_daily_summary("Daily Performance Summary", "Equity up 1.5%")

    mock_send_email.assert_called_once_with(
        "Daily Performance Summary", "Equity up 1.5%"
    )


def test_send_telegram_message(alerting, mocker):
    mock_requests_post = mocker.patch("requests.post")

    alerting._send_telegram_message("Test Telegram message")

    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    assert "api.telegram.org" in args[0]
    assert kwargs["data"]["text"] == "Test Telegram message"


def test_send_email(alerting, mocker):
    # Just check if it logs the attempt for now, as real SMTP is not configured
    mock_logging_info = mocker.patch("logging.info")

    alerting._send_email("Test Subject", "Test Body")

    mock_logging_info.assert_called_once()
    assert "Email sent" in mock_logging_info.call_args[0][0]
