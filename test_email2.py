"""
Email Testing Script - Alternative methods
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import settings

# Email settings from .env
SMTP_HOST = settings.smtp_host
SMTP_USER = settings.smtp_user
SMTP_PASSWORD = settings.smtp_password
TO_EMAIL = settings.admin_email

def test_port_587_starttls():
    """Test SMTP with STARTTLS on port 587"""
    print("\n" + "=" * 50)
    print("TEST 1: Port 587 with STARTTLS")
    print("=" * 50)
    try:
        print("Connecting...")
        server = smtplib.SMTP(SMTP_HOST, 587, timeout=10)
        print("Connected!")
        print("Starting TLS...")
        server.starttls()
        print("TLS started!")
        print("Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("Login successful!")
        server.quit()
        return True
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False

def test_port_465_ssl():
    """Test SMTP with SSL on port 465"""
    print("\n" + "=" * 50)
    print("TEST 2: Port 465 with SSL")
    print("=" * 50)
    try:
        print("Connecting with SSL...")
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(SMTP_HOST, 465, context=context, timeout=10)
        print("Connected!")
        print("Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("Login successful!")
        server.quit()
        return True
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False

def send_test_email_ssl():
    """Send a test email using SSL"""
    print("\n" + "=" * 50)
    print("Sending test email via SSL (port 465)...")
    print("=" * 50)
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = TO_EMAIL
        msg['Subject'] = "Test Email - Report to Reveal"
        
        body = f"""
        <html>
        <body>
            <h2>Test Email Success!</h2>
            <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Your email configuration is working!</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context, timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            print("[SUCCESS] Email sent!")
            return True
            
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("Testing email connection methods...")
    print(f"Using: {SMTP_USER}")
    print(f"To: {TO_EMAIL}")
    
    # Test both methods
    result_587 = test_port_587_starttls()
    result_465 = test_port_465_ssl()
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print("=" * 50)
    print(f"Port 587 (STARTTLS): {'OK' if result_587 else 'FAILED'}")
    print(f"Port 465 (SSL):      {'OK' if result_465 else 'FAILED'}")
    
    if result_465 and not result_587:
        print("\nRecommendation: Use SSL on port 465 instead of STARTTLS on port 587")
        print("Update your .env file:")
        print("  SMTP_PORT=465")
        print("  SMTP_USE_TLS=false  # SSL is used instead")
        
        # Send test email automatically
        print("\nSending test email via SSL...")
        send_test_email_ssl()
    elif result_587:
        print("\nPort 587 works! Your current configuration should work.")
    else:
        print("\nBoth methods failed. Check:")
        print("  - Your App Password is correct")
        print("  - Your firewall/antivirus is not blocking SMTP")
        print("  - Your network allows SMTP connections")

