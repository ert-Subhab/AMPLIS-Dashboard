"""
Email Sender
Sends automated email reports
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import List, Dict
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailSender:
    """Send email reports"""
    
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        """
        Initialize email sender
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port number
            sender_email: Sender email address
            sender_password: Sender email password (use app password for Gmail)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_report(self, recipient_emails: List[str], processed_data: Dict, attachment_path: str = None):
        """
        Send email report
        
        Args:
            recipient_emails: List of recipient email addresses
            processed_data: Processed data dictionary
            attachment_path: Optional path to HTML report attachment
        """
        try:
            # Create email body
            email_body = self._create_email_body(processed_data)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipient_emails)
            msg['Subject'] = f"Outreach Performance Report - {datetime.now().strftime('%B %d, %Y')}"
            
            # Add body
            msg.attach(MIMEText(email_body, 'html'))
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read(), _subtype='html')
                    attachment.add_header('Content-Disposition', 'attachment', 
                                        filename=f'outreach_report_{datetime.now().strftime("%Y%m%d")}.html')
                    msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email report sent to {len(recipient_emails)} recipients")
        except Exception as e:
            logger.error(f"Error sending email report: {e}")
    
    def _create_email_body(self, data: Dict) -> str:
        """Create HTML email body"""
        
        combined = data['combined_metrics']
        performance = data['performance_summary']
        recommendations = data['recommendations']
        linkedin = data['linkedin']
        email_data = data['email']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .metric {{
            display: inline-block;
            width: 48%;
            padding: 15px;
            margin: 1%;
            background: white;
            border-radius: 5px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        
        .performance-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .recommendations {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        
        .recommendations h3 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        
        .recommendation {{
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .recommendation:last-child {{
            border-bottom: none;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Outreach Performance Report</h1>
        <p>{datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <div class="metric-value">{combined['total_outreach_actions']:,}</div>
            <div class="metric-label">Total Outreach</div>
        </div>
        <div class="metric">
            <div class="metric-value">{combined['total_responses']:,}</div>
            <div class="metric-label">Total Responses</div>
        </div>
        <div class="metric">
            <div class="metric-value">{combined['overall_response_rate']}%</div>
            <div class="metric-label">Response Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{combined['total_active_campaigns']}</div>
            <div class="metric-label">Active Campaigns</div>
        </div>
    </div>
    
    <div class="section">
        <h2>💼 LinkedIn Performance</h2>
        <div class="performance-row">
            <span>Invites Sent:</span>
            <strong>{linkedin['total_invites_sent']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Invites Accepted:</span>
            <strong>{linkedin['total_invites_accepted']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Acceptance Rate:</span>
            <strong>{linkedin['acceptance_rate']}%</strong>
        </div>
        <div class="performance-row">
            <span>Messages Sent:</span>
            <strong>{linkedin['total_messages_sent']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Replies:</span>
            <strong>{linkedin['total_replies']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Reply Rate:</span>
            <strong>{linkedin['reply_rate']}%</strong>
        </div>
    </div>
    
    <div class="section">
        <h2>📧 Email Performance</h2>
        <div class="performance-row">
            <span>Emails Sent:</span>
            <strong>{email_data['total_emails_sent']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Delivered:</span>
            <strong>{email_data['total_emails_delivered']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Delivery Rate:</span>
            <strong>{email_data['delivery_rate']}%</strong>
        </div>
        <div class="performance-row">
            <span>Opened:</span>
            <strong>{email_data['total_opened']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Open Rate:</span>
            <strong>{email_data['open_rate']}%</strong>
        </div>
        <div class="performance-row">
            <span>Replies:</span>
            <strong>{email_data['total_replied']:,}</strong>
        </div>
        <div class="performance-row">
            <span>Reply Rate:</span>
            <strong>{email_data['reply_rate']}%</strong>
        </div>
    </div>
    
    <div class="recommendations">
        <h3>💡 Recommendations</h3>
        {''.join([f'<div class="recommendation">{rec}</div>' for rec in recommendations])}
    </div>
    
    <div class="footer">
        <p>See the attached HTML report for detailed charts and visualizations.</p>
        <p>Generated by Outreach Reporting Automation</p>
    </div>
</body>
</html>
        """
        
        return html
    
    def test_connection(self) -> bool:
        """
        Test email connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            
            logger.info("✅ Email connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Email connection failed: {e}")
            return False
