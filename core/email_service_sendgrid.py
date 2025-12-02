"""
Email service using SendGrid API (alternative to SMTP)
Works when SMTP ports are blocked
"""
import logging
import requests
import base64
from pathlib import Path
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SendGridEmailService:
    """Email service using SendGrid API"""
    
    def __init__(self, api_key: str, from_email: str, admin_email: str = None):
        self.api_key = api_key
        self.from_email = from_email
        self.admin_email = admin_email
        self.api_url = "https://api.sendgrid.com/v3/mail/send"
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.api_key and self.from_email)
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """Send email via SendGrid API"""
        if not self.is_configured():
            logger.warning("SendGrid not configured")
            return False
        
        try:
            # Build email data
            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": self.from_email},
                "subject": subject,
                "content": [{"type": "text/html", "value": body_html}]
            }
            
            # Add attachments
            if attachments:
                attachment_list = []
                for file_path in attachments:
                    if isinstance(file_path, str):
                        file_path = Path(file_path)
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            content = base64.b64encode(f.read()).decode()
                            attachment_list.append({
                                "content": content,
                                "filename": file_path.name,
                                "type": "application/octet-stream",
                                "disposition": "attachment"
                            })
                if attachment_list:
                    data["attachments"] = attachment_list
            
            # Send request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.api_url, json=data, headers=headers, timeout=30)
            
            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_report_to_customer(
        self,
        to_email: str,
        customer_name: str,
        report_path: Path,
        document_name: str,
        compliance_score: float,
        document_type: str = "report"
    ) -> bool:
        """Send analysis report to customer"""
        doc_type_label = "Lake Management Plan" if document_type == "plan" else "Lake Report"
        subject = f"Your {doc_type_label} Analysis - Report to Reveal"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Dear {customer_name},</h2>
            <p>Thank you for submitting your {doc_type_label} for analysis.</p>
            <p>We have completed our comprehensive evaluation of <strong>{document_name}</strong>.</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Analysis Summary:</h3>
                <ul>
                    <li><strong>Document Type:</strong> {doc_type_label}</li>
                    <li><strong>Compliance Score:</strong> {compliance_score:.1f}%</li>
                    <li><strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                </ul>
            </div>
            <p>The attached report contains detailed analysis and recommendations.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
            The Report to Reveal Team<br>
            Email: action@reporttoreveal.com
            </p>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            attachments=[report_path] if report_path and Path(report_path).exists() else None
        )
    
    def send_admin_notification(
        self,
        customer_name: str,
        customer_email: str,
        organization: str,
        document_names: List[str],
        submission_id: str
    ) -> bool:
        """Send notification to admin"""
        if not self.admin_email:
            return False
        
        subject = f"New Submission - {customer_name} ({organization})"
        body_html = f"""
        <html>
        <body>
            <h2>New Document Submission</h2>
            <p><strong>Customer:</strong> {customer_name}</p>
            <p><strong>Email:</strong> {customer_email}</p>
            <p><strong>Organization:</strong> {organization}</p>
            <p><strong>Documents:</strong> {', '.join(document_names)}</p>
            <p><strong>Submission ID:</strong> {submission_id}</p>
        </body>
        </html>
        """
        
        return self._send_email(self.admin_email, subject, body_html)

    def send_processing_complete_notification(
        self,
        submission_id: str,
        document_name: str,
        compliance_score: float,
        report_path: Path
    ) -> bool:
        """Notify admin when processing is complete"""
        if not self.admin_email:
            return False
        
        subject = f"Analysis Complete - {document_name}"
        body_html = f"""
        <html>
        <body>
            <h2>Document Analysis Complete</h2>
            <p><strong>Document:</strong> {document_name}</p>
            <p><strong>Score:</strong> {compliance_score:.1f}%</p>
        </body>
        </html>
        """
        
        return self._send_email(
            self.admin_email, subject, body_html, 
            [report_path] if report_path and Path(report_path).exists() else None
        )

