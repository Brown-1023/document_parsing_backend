# Email Setup Guide

## 📧 Configuring Email for Report to Reveal System

The system can automatically send analysis reports to customers and notifications to administrators. Follow this guide to set up email functionality.

## 1. Email Configuration Options

Add these settings to your `backend/.env` file:

```env
# Email Server Configuration
SMTP_HOST=smtp.gmail.com        # Your email server
SMTP_PORT=587                   # Usually 587 for TLS, 465 for SSL
SMTP_USER=your_email@gmail.com  # Your email address
SMTP_PASSWORD=your_app_password # App-specific password (NOT regular password)
SMTP_USE_TLS=true               # Use TLS encryption
FROM_EMAIL=your_email@gmail.com # From address for sent emails
ADMIN_EMAIL=admin@company.com   # Admin email for notifications

# Email Behavior
SEND_REPORTS_AUTOMATICALLY=false # true = send immediately, false = require manual approval
```

## 2. Provider-Specific Settings

### Gmail
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
# Requires App Password - see below
```

### Outlook/Office365
```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### Yahoo
```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

## 3. Getting App Passwords

### Gmail App Password Setup
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already enabled
3. Click on "2-Step Verification"
4. Scroll down and click "App passwords"
5. Select "Mail" and your device
6. Copy the 16-character password
7. Use this as SMTP_PASSWORD (without spaces)

### Outlook App Password
1. Go to https://account.microsoft.com/security
2. Enable two-step verification
3. Click "More security options"
4. Under "App passwords", create a new password
5. Use this as SMTP_PASSWORD

## 4. Email Features

### When Email is Configured:

1. **Customer Emails** - After analysis completes:
   - Sends report as Word attachment
   - Includes compliance score and summary
   - Provides recommendations and next steps
   - Can be automatic or manual

2. **Admin Notifications**:
   - When new documents are uploaded
   - When analysis completes
   - Includes customer info and submission details
   - Attachments of generated reports

3. **Manual Sending**:
   - Use the API endpoint: `POST /api/v1/send-report/{analysis_id}`
   - Or through the admin dashboard

## 5. Testing Email Configuration

1. Check if email is configured:
```bash
curl http://localhost:8000/api/v1/email-status
```

2. Response will show:
```json
{
  "configured": true,
  "smtp_host": "smtp.gmail.com",
  "automatic_sending": false,
  "admin_email": "admin@company.com"
}
```

## 6. Troubleshooting

### Email Not Sending?
1. Check `.env` file has correct settings
2. Verify app password (not regular password)
3. Check firewall allows outgoing SMTP
4. Look for error messages in backend logs

### Common Issues:
- **535 Authentication Failed**: Wrong password or need app password
- **Connection Timeout**: Firewall blocking or wrong host/port
- **TLS Error**: Try changing SMTP_USE_TLS to false

## 7. Email Templates

The system sends professional HTML emails with:
- Company branding
- Clear formatting
- Call-to-action buttons
- Contact information

Templates are located in:
- `backend/core/email_service.py`

## 8. Security Notes

- Never commit `.env` file to version control
- Use app passwords, not regular passwords
- Consider using environment variables in production
- Regularly rotate passwords
- Monitor for failed send attempts

## 9. Email Workflow

```
Document Upload
    ↓
Admin Notification Email → "New submission from [Customer]"
    ↓
Document Processing
    ↓
Analysis Complete
    ↓
If SEND_REPORTS_AUTOMATICALLY = true:
    → Customer Email with Report
    → Admin Confirmation Email
If SEND_REPORTS_AUTOMATICALLY = false:
    → Admin Review Email
    → Manual Send via Dashboard/API
```

## 10. Example Customer Email

**Subject**: Your Lake Report Analysis - Report to Reveal

**Body**: 
- Personalized greeting
- Compliance score summary
- Key findings
- Attached Word report
- Recommendations
- Next steps
- Contact information

---

For questions or issues, contact the development team.
