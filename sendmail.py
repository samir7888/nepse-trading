#!/usr/bin/env python3
"""
Legacy sendmail.py - Updated to use environment variables for security
For the full trading system email, use send_trading_email.py instead
"""
import smtplib
import os
from email.mime.text import MIMEText

# Use environment variables for security (don't hardcode credentials)
EMAIL = os.getenv('EMAIL_USER', 'basnetsameer78@gmail.com')
PASSWORD = os.getenv('EMAIL_PASSWORD', 'fthp aikl cozp ocpq')  # Use app password
TO_EMAIL = os.getenv('TO_EMAIL', 'basnetsameer78@gmail.com')

def send_simple_notification(message="Your cron job ran successfully."):
    """Send a simple notification email"""
    try:
        msg = MIMEText(message)
        msg["Subject"] = "NEPSE Trading System - Cron Job Update"
        msg["From"] = EMAIL
        msg["To"] = TO_EMAIL

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)

        print("✅ Simple notification email sent")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

if __name__ == "__main__":
    send_simple_notification()