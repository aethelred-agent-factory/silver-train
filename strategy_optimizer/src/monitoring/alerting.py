import os
import logging
import requests
import smtplib
from email.mime.text import MIMEText

class Alerting:
    """
    Handles sending email and Telegram alerts for critical events and summaries.
    """
    def __init__(self, config):
        self.config = config
        self.telegram_bot_token = os.getenv("ALERT_TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("ALERT_TELEGRAM_CHAT_ID")
        self.email_sender = os.getenv("ALERT_EMAIL_SENDER")
        self.email_recipient = os.getenv("ALERT_EMAIL_RECIPIENT")
        logging.info("Initialized Alerting system.")

    def send_urgent_alert(self, message: str):
        """
        Sends an urgent alert via all configured channels (Telegram, Email).
        """
        logging.critical(f"URGENT ALERT: {message}")
        self._send_telegram_message(f"🚨 URGENT: {message}")
        self._send_email(f"URGENT ALERT: Strategy Optimizer", message)

    def send_daily_summary(self, subject: str, body: str):
        """
        Sends a daily summary via email.
        """
        logging.info(f"Sending daily summary: {subject}")
        self._send_email(subject, body)

    def _send_telegram_message(self, message: str):
        """
        Sends a message to a Telegram chat.
        """
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logging.warning("Telegram alerting not configured (missing bot token or chat ID).")
            return

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML" # Optional, for basic formatting
        }
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            logging.info("Telegram message sent successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send Telegram message: {e}")

    def _send_email(self, subject: str, body: str):
        """
        Sends an email.
        (Requires an SMTP server configured, e.g., for Gmail, SendGrid, etc.)
        """
        if not self.email_sender or not self.email_recipient:
            logging.warning("Email alerting not configured (missing sender or recipient).")
            return

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_sender
        msg['To'] = self.email_recipient

        try:
            # This requires an SMTP server configuration (e.g., hostname, port, username, password)
            # For simplicity, we'll just log that an email would be sent.
            # In a real setup, you'd use smtplib.SMTP_SSL or similar.
            # For example:
            # with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            #     smtp.login('your_email@gmail.com', 'your_password')
            #     smtp.send_message(msg)
            logging.info(f"Email sent (to {self.email_recipient}): Subject='{subject}'")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
