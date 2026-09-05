import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to_email: str, subject: str, body: str) -> bool:
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        print("SendGrid Error: SENDGRID_API_KEY is not set in environment variables.")
        return False

    try:
        sg = SendGridAPIClient(api_key)
        message = Mail(
            from_email=os.getenv("FROM_EMAIL", "noreply@yourdomain.com"),
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        sg.send(message)
        return True
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return False

