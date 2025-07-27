import openai
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Default model and settings
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 300

def send_prompt(prompt_text: str, model=DEFAULT_MODEL, temperature=0.7):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message['content'].strip()

    except Exception as e:
        return f"[ERROR] {str(e)}"
