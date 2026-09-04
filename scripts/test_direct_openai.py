import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")

from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=15.0,
)

async def main():
    print(f"Testing direct chat completion with model {model_name}...", flush=True)
    try:
        resp = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'hello world' and nothing else."}],
        )
        print("Response received:", resp.choices[0].message.content, flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
