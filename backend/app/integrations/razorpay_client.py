import razorpay
from app.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

# Initialize the Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_payment_link(invoice_id: int, amount: float, customer_name: str, customer_email: str) -> tuple[str, str]:
    """Generates a unique Razorpay payment link for an invoice."""
    
    # Razorpay expects amounts in paise (multiply INR by 100)
    data = {
        "amount": int(amount * 100),
        "currency": "INR",
        "accept_partial": False,
        "reference_id": str(invoice_id),
        "description": f"Outstanding Balance for Invoice #{invoice_id}",
        "customer": {
            "name": customer_name,
            "email": customer_email
        },
        "notify": {
            "email": False, # We handle our own email outreach
            "sms": False
        },
        "reminder_enable": False
    }
    
    try:
        response = client.payment_link.create(data) # type: ignore
        # Return both the ID and the URL
        return response.get("id"), response.get("short_url") 
    except Exception as e:
        print(f"Razorpay Link Creation Error: {e}")
        return "", ""
