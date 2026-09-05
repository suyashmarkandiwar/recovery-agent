from app.integrations.groq_client import generate_message


def draft_recovery_email(customer_name: str, amount: float, invoice_id: int, tone: str, days_passed: int) -> dict:
    # 1. AI only generates the custom tone paragraph
    prompt = f"Giving a <think></think> block and the content inside it in reply is strictly PROHIBITED just Write a single, strictly {tone} 2 lines paragraph urging customer to pay their balance. Do not include any date for remitence of the amount"
    
    try:
        raw_response = generate_message(prompt)
    except Exception as e:
        return {"error": True, "raw": str(e)}

    # Clean up <think> blocks if Qwen/DeepSeek still uses them
    think_end = raw_response.rfind('</think>')  
    ai_paragraph = raw_response[think_end + len('</think>'):].strip() if think_end != -1 else raw_response.strip()

    # 2. Python handles the structure deterministically
    subject = f"Outstanding Balance Notice: {customer_name}"
    
    body = f"""Dear {customer_name} Accounts Payable,

This is a formal notice that your balance of ₹{amount} for Invoice #{invoice_id} is exactly {days_passed} days overdue.

{ai_paragraph}

Please process your secure payment using the following link: {{PAYMENT_LINK}}

If you have already settled this invoice, kindly disregard this notice.

Sincerely,
Finance Department"""

    return {"email_subject": subject, "email_body": body}