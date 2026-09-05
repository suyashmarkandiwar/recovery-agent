from groq import Groq
from app.config import GROQ_API_KEY
import re

client = Groq(api_key=GROQ_API_KEY)

def generate_message(prompt: str) -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a professional debt collection assistant. Provide only the final email paragraph. NEVER use <think> tags. NEVER output your reasoning process."},
            {"role": "user", "content": prompt}
        ],
        model="qwen/qwen3.8-27b",
        max_tokens=900,
        temperature=0.1
    )
    raw = response.choices[0].message.content or ""
    
    # Bulletproof removal: take everything AFTER the closing tag
    if "</think>" in raw:
        cleaned = raw.split("</think>")[-1].strip()
    else:
        # Fallback just in case there's an opening tag but it got cut off
        cleaned = re.sub(r"<think>.*?(</think>|$)", "", raw, flags=re.DOTALL).strip()
        
    return cleaned
