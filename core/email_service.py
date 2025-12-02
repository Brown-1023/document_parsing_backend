"""
Email service for sending reports and notifications
"""

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email notifications"""
    
    def __init__(self, settings):
        """Initialize email service with settings"""
        self.settings = settings
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email or settings.smtp_user
        self.admin_email = settings.admin_email
        self.use_tls = getattr(settings, 'smtp_use_tls', True)
        
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(
            self.smtp_host and 
            self.smtp_port and 
            self.smtp_user and 
            self.smtp_password
        )
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """Internal method to send email"""
        if not self.is_configured():
            logger.warning("Email service not configured")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            # Add HTML body
            msg.attach(MIMEText(body_html, 'html'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            attachment = MIMEApplication(f.read())
                            attachment.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=file_path.name
                            )
                            msg.attach(attachment)
            
            # Connect and send
            # Use SSL for port 465, STARTTLS for port 587
            if self.smtp_port == 465:
                # SSL connection
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # STARTTLS connection (port 587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
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
            
            <p>We have completed our comprehensive evaluation of <strong>{document_name}</strong> 
            against our evidence-based best practices.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Analysis Summary:</h3>
                <ul>
                    <li><strong>Document Type:</strong> {doc_type_label}</li>
                    <li><strong>Compliance Score:</strong> {compliance_score:.1f}%</li>
                    <li><strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                </ul>
            </div>
            
            <p>The attached Word document contains:</p>
            <ul>
                <li>Detailed parameter-by-parameter analysis</li>
                <li>Identification of missing critical metrics</li>
                <li>Recommendations for improvement</li>
                <li>Action plan to convert your {doc_type_label} into a Lake Management ACTION Plan</li>
            </ul>
            
            <p><strong>Next Steps:</strong></p>
            <ol>
                <li>Review the attached analysis report</li>
                <li>Focus on the "High Priority Actions" section</li>
                <li>Contact us to discuss implementing the recommendations</li>
            </ol>
            
            <p>Remember our motto: <em>"Report to Reveal, Not Conceal"</em></p>
            
            <p>If you have any questions about the analysis or would like to discuss 
            converting your plan into an ACTION Plan, please don't hesitate to contact us.</p>
            
            <hr style="border: 1px solid #ddd; margin: 30px 0;">
            
            <p style="color: #666; font-size: 12px;">
            Best regards,<br>
            The Report to Reveal Team<br>
            Email: action@reporttoreveal.com<br>
            Phone: 1-800-LAKE-FIX<br>
            Website: www.reporttoreveal.com
            </p>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            attachments=[report_path] if report_path.exists() else None
        )
    
    def send_admin_notification(
        self,
        customer_name: str,
        customer_email: str,
        organization: str,
        document_names: List[str],
        submission_id: str
    ) -> bool:
        """Send notification to admin when new documents are uploaded"""
        
        if not self.admin_email:
            logger.warning("Admin email not configured")
            return False
        
        subject = f"New Document Submission - {customer_name} ({organization})"
        
        doc_list = "\n".join([f"  • {name}" for name in document_names])
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>New Document Submission Received</h2>
            
            <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Submission Details:</h3>
                <table style="width: 100%;">
                    <tr>
                        <td style="padding: 5px;"><strong>Submission ID:</strong></td>
                        <td>{submission_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Customer Name:</strong></td>
                        <td>{customer_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Email:</strong></td>
                        <td>{customer_email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Organization:</strong></td>
                        <td>{organization}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;"><strong>Time:</strong></td>
                        <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
            </div>
            
            <h3>Documents Submitted:</h3>
            <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 3px;">
{doc_list}
            </pre>
            
            <p><strong>Action Required:</strong></p>
            <ul>
                <li>Documents are being processed automatically</li>
                <li>Analysis reports will be generated shortly</li>
                <li>Review reports before sending to customer (if manual review is enabled)</li>
            </ul>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated notification from the Report to Reveal analysis system.
            </p>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=self.admin_email,
            subject=subject,
            body_html=body_html
        )
    
    def send_processing_complete_notification(
        self,
        submission_id: str,
        document_name: str,
        compliance_score: float,
        report_path: Path
    ) -> bool:
        """Notify admin when document processing is complete"""
        
        if not self.admin_email:
            return False
        
        subject = f"Analysis Complete - {document_name}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Document Analysis Complete</h2>
            
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px;">
                <p><strong>Document:</strong> {document_name}</p>
                <p><strong>Submission ID:</strong> {submission_id}</p>
                <p><strong>Compliance Score:</strong> {compliance_score:.1f}%</p>
                <p><strong>Report Generated:</strong> {report_path.name}</p>
            </div>
            
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Review the generated report for accuracy</li>
                <li>Make any necessary edits in Word</li>
                <li>Send to customer or approve automatic sending</li>
            </ul>
            
            <p style="margin-top: 20px;">
            <a href="http://localhost:3000/admin/submissions/{submission_id}" 
               style="background-color: #4CAF50; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px;">
                View in Admin Dashboard
            </a>
            </p>
        </body>
        </html>
        """
        
        return self._send_email(
            to_email=self.admin_email,
            subject=subject,
            body_html=body_html,
            attachments=[report_path] if report_path.exists() else None
        )

    def send_lake_assessment_notification(
        self,
        customer_name: str,
        customer_email: str,
        lake_name: str,
        report_path: str,
        year_range: str
    ) -> bool:
        """Send Lake Assessment trend analysis report to customer"""
        
        subject = f"Lake Assessment for {lake_name} - Multi-Year Trend Analysis"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #003366; color: white; padding: 20px; text-align: center;">
                <h1>Lake Assessment Report</h1>
                <p style="margin: 0;">Multi-Year Trend Analysis</p>
            </div>
            
            <div style="padding: 20px; background-color: #f9f9f9;">
                <p>Dear {customer_name},</p>
                
                <p>Your <strong>Lake Assessment</strong> for <strong>{lake_name}</strong> is complete!</p>
                
                <div style="background-color: white; padding: 15px; border-left: 4px solid #003366; margin: 20px 0;">
                    <h3 style="color: #003366; margin-top: 0;">What is a Lake Assessment?</h3>
                    <p>A Lake Assessment analyzes multiple years of data to identify trends in:</p>
                    <ul>
                        <li>Water quality parameters</li>
                        <li>Hypoxia development</li>
                        <li>Nutrient levels</li>
                        <li>Overall lake trajectory</li>
                    </ul>
                    <p><strong>Analysis Period:</strong> {year_range}</p>
                </div>
                
                <p>The attached report provides:</p>
                <ul>
                    <li>📈 Trend analysis for key parameters</li>
                    <li>📊 Year-by-year comparisons</li>
                    <li>🔍 Key findings and insights</li>
                    <li>💡 Data-driven recommendations</li>
                </ul>
                
                <div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Why This Matters:</strong></p>
                    <p>Understanding trends over time is crucial for effective lake management. 
                    This assessment reveals whether your lake is improving, stable, or degrading, 
                    allowing you to make informed management decisions.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 18px; color: #003366;">
                        <strong>Need help interpreting these trends?</strong>
                    </p>
                    <p>Our experts are available to discuss your Lake Assessment and develop 
                    targeted intervention strategies.</p>
                </div>
                
                <hr style="border: 1px solid #ddd; margin: 30px 0;">
                
                <p style="text-align: center; color: #666;">
                    <em>Report to Reveal, Not Conceal™</em><br>
                    Science-based lake management solutions
                </p>
            </div>
        </body>
        </html>
        """
        
        # Attach the Lake Assessment report
        attachments = []
        if Path(report_path).exists():
            attachments.append(report_path)
        
        return self._send_email(
            to_email=customer_email,
            subject=subject,
            body_html=body_html,
            attachments=attachments
        )

def initialize_email_service(settings):
    """Initialize the global email service instance"""
    global email_service
    email_service = EmailService(settings)
    return email_service
