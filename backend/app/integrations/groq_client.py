from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def generate_message(prompt: str) -> str:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="qwen/qwen3.6-27b",
        max_tokens=4096,  # Prevents the JSON from being cut off
        temperature=0.1   # Forces the AI to strictly follow your structure
    )
    return response.choices[0].message.content or ""