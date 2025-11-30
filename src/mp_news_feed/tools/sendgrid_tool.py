from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content, Email, To
import os


class SendGridToolInput(BaseModel):
    """Input schema for SendGrid Email Tool."""
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    html_content: str = Field(..., description="HTML content of the email")
    from_email: str = Field(default=None, description="Sender email (optional, uses default if not provided)")


class SendGridEmailTool(BaseTool):
    name: str = "SendGrid Email Sender"
    description: str = (
        "Sends professional emails using SendGrid. Use this tool to distribute "
        "reports, summaries, or notifications to team members via email. "
        "Requires recipient email, subject, and HTML content."
    )
    args_schema: Type[BaseModel] = SendGridToolInput

    def _run(self, to_email: str, subject: str, html_content: str, from_email: str = None) -> str:
        """Send an email using SendGrid API."""
        try:
            # Get API key from environment variable
            api_key = os.getenv('SENDGRID_API_KEY')
            if not api_key:
                return "Error: SENDGRID_API_KEY environment variable not set"
            
            # Create SendGrid client
            sg = SendGridAPIClient(api_key)
            
            # Create the email message
            message = Mail(
                from_email=Email('zampogna.ulysse@gmail.com'),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Send the email
            response = sg.send(message)
            
            # Return success confirmation
            return (
                f"✓ Email sent successfully!\n"
                f"Status Code: {response.status_code}\n"
                f"From: {from_email}\n"
                f"To: {to_email}\n"
                f"Subject: {subject}\n"
                f"Timestamp: {response.headers.get('Date', 'N/A')}"
            )
            
        except Exception as e:
            return f"Error sending email: {str(e)}"

