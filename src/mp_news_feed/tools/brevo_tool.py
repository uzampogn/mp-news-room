from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import brevo_python
from brevo_python.rest import ApiException
import os


class BrevoToolInput(BaseModel):
    """Input schema for Brevo Email Tool."""
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    html_content: str = Field(..., description="HTML content of the email")


class BrevoEmailTool(BaseTool):
    name: str = "Brevo Email Sender"
    description: str = (
        "Sends professional emails using Brevo. Use this tool to distribute "
        "reports, summaries, or notifications to team members via email. "
        "Requires recipient email, subject, and HTML content."
    )
    args_schema: Type[BaseModel] = BrevoToolInput

    def _run(self, to_email: str, subject: str, html_content: str) -> str:
        """Send an email using Brevo API."""
        try:
            # Get API key from environment variable
            api_key = os.getenv('BREVO_API_KEY')
            if not api_key:
                return "Error: BREVO_API_KEY environment variable not set"

            # Configure Brevo API client
            configuration = brevo_python.Configuration()
            configuration.api_key['api-key'] = api_key

            # Create API instance
            api_instance = brevo_python.TransactionalEmailsApi(
                brevo_python.ApiClient(configuration)
            )

            # Create the email message
            send_smtp_email = brevo_python.SendSmtpEmail(
                sender={"email": "zampogna.ulysse@gmail.com", "name": "MP News Feed"},
                to=[{"email": to_email}],
                subject=subject,
                html_content=html_content
            )

            # Send the email
            response = api_instance.send_transac_email(send_smtp_email)

            # Return success confirmation
            return (
                f"Email sent successfully!\n"
                f"Message ID: {response.message_id}\n"
                f"To: {to_email}\n"
                f"Subject: {subject}"
            )

        except ApiException as e:
            return f"Error sending email (API): {str(e)}"
        except Exception as e:
            return f"Error sending email: {str(e)}"
