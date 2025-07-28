import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 300

def send_prompt(prompt_text: str, model="gpt-3.5-turbo"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        message = response.choices[0].message.content.strip()
        usage = response.usage
        return message, usage
    except Exception as e:
        return f"[ERROR] {str(e)}", None

def estimate_cost(usage, model):
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    if model == "gpt-3.5-turbo":
        return total_tokens / 1000 * 0.0015
    elif model == "gpt-4":
        # Based on typical 2025 pricing
        return (input_tokens / 1000 * 0.01) + (output_tokens / 1000 * 0.03)
    return 0.0
