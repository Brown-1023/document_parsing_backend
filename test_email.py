"""
Email Testing Script
Tests email configuration and sends a test email
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from core.email_service import EmailService

def test_email_configuration():
    """Test email configuration"""
    print("=" * 60)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Check settings
    print("\n1. Checking email settings from .env:")
    print(f"   SMTP_HOST: {settings.smtp_host or '(not set)'}")
    print(f"   SMTP_PORT: {settings.smtp_port}")
    print(f"   SMTP_USER: {settings.smtp_user or '(not set)'}")
    print(f"   SMTP_PASSWORD: {'*' * len(settings.smtp_password) if settings.smtp_password else '(not set)'}")
    print(f"   SMTP_USE_TLS: {settings.smtp_use_tls}")
    print(f"   FROM_EMAIL: {settings.from_email or '(not set)'}")
    print(f"   ADMIN_EMAIL: {settings.admin_email or '(not set)'}")
    print(f"   SEND_REPORTS_AUTOMATICALLY: {settings.send_reports_automatically}")
    
    # Initialize email service
    email_service = EmailService(settings)
    
    print("\n2. Email service configuration status:")
    if email_service.is_configured():
        print("   [OK] Email service is properly configured")
    else:
        print("   [ERROR] Email service is NOT configured")
        print("\n   Missing required settings:")
        if not settings.smtp_host:
            print("   - SMTP_HOST is not set")
        if not settings.smtp_port:
            print("   - SMTP_PORT is not set")
        if not settings.smtp_user:
            print("   - SMTP_USER is not set")
        if not settings.smtp_password:
            print("   - SMTP_PASSWORD is not set")
        return False
    
    return True

def send_test_email():
    """Send a test email"""
    print("\n3. Attempting to send test email...")
    
    email_service = EmailService(settings)
    
    if not email_service.is_configured():
        print("   Cannot send test email - email service not configured")
        return False
    
    # Determine recipient
    test_recipient = settings.admin_email or settings.smtp_user
    if not test_recipient:
        print("   No recipient email available (neither ADMIN_EMAIL nor SMTP_USER set)")
        return False
    
    print(f"   Sending test email to: {test_recipient}")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import datetime
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = email_service.from_email
        msg['To'] = test_recipient
        msg['Subject'] = "Test Email - Report to Reveal System"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Test Email - Report to Reveal</h2>
            <p>This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>If you received this email, your email configuration is working correctly!</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
            Configuration used:<br>
            - SMTP Host: {email_service.smtp_host}<br>
            - SMTP Port: {email_service.smtp_port}<br>
            - TLS: {email_service.use_tls}<br>
            - From: {email_service.from_email}
            </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body_html, 'html'))
        
        # Connect and send
        print(f"   Connecting to {email_service.smtp_host}:{email_service.smtp_port}...")
        
        # Use SSL for port 465, STARTTLS for port 587
        if email_service.smtp_port == 465:
            import ssl
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(email_service.smtp_host, email_service.smtp_port, context=context, timeout=30) as server:
                server.set_debuglevel(1)  # Enable debug output
                print("   SSL Connection established")
                
                print("   Logging in...")
                server.login(email_service.smtp_user, email_service.smtp_password)
                print("   Login successful")
                
                print("   Sending message...")
                server.send_message(msg)
                print("   [SUCCESS] Email sent successfully!")
        else:
            with smtplib.SMTP(email_service.smtp_host, email_service.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)  # Enable debug output
                print("   Connection established")
                
                if email_service.use_tls:
                    print("   Starting TLS...")
                    server.starttls()
                    print("   TLS enabled")
                
                print("   Logging in...")
                server.login(email_service.smtp_user, email_service.smtp_password)
                print("   Login successful")
                
                print("   Sending message...")
                server.send_message(msg)
                print("   [SUCCESS] Email sent successfully!")
            
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n   [ERROR] AUTHENTICATION ERROR: {e}")
        print("\n   Possible causes:")
        print("   - Wrong username or password")
        print("   - For Gmail: You need to use an App Password, not your regular password")
        print("   - For Gmail: Enable 2-Step Verification first, then create an App Password")
        print("   - Check if 'Less secure app access' is needed (not recommended)")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"\n   [ERROR] CONNECTION ERROR: {e}")
        print("\n   Possible causes:")
        print("   - Wrong SMTP_HOST or SMTP_PORT")
        print("   - Firewall blocking outgoing connections")
        print("   - Network connectivity issues")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n   [ERROR] SMTP ERROR: {e}")
        return False
        
    except Exception as e:
        print(f"\n   [ERROR] UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("REPORT TO REVEAL - EMAIL SYSTEM TEST")
    print("=" * 60)
    
    # Test configuration
    config_ok = test_email_configuration()
    
    if not config_ok:
        print("\n" + "=" * 60)
        print("HOW TO FIX:")
        print("=" * 60)
        print("""
1. Create or edit the .env file in the backend folder with:

   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   SMTP_USE_TLS=true
   FROM_EMAIL=your_email@gmail.com
   ADMIN_EMAIL=admin@yourcompany.com
   SEND_REPORTS_AUTOMATICALLY=false

2. For Gmail, you need an App Password:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification
   - Go to App passwords
   - Generate a new app password for 'Mail'
   - Use that 16-character password (no spaces)
        """)
        return
    
    # Ask to send test email
    print("\n" + "-" * 60)
    response = input("Would you like to send a test email? (y/n): ").strip().lower()
    
    if response == 'y':
        send_test_email()
    else:
        print("   Skipping test email")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

