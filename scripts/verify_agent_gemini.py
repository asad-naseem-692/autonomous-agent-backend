import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")

print(f"Testing Gemini Agents SDK integration with model: {model_name}")
print(f"API Key present: {bool(api_key)} (len: {len(api_key) if api_key else 0})")

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool

gemini_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Test 1: Simple read tool
@function_tool
def test_find_customer(name: str) -> str:
    """Finds a customer by name in the system."""
    print(f"--> [TOOL EXECUTED] test_find_customer called with name={name}")
    return f'{{"id": "cust-123", "name": "{name}", "email": "{name.lower()}@example.com"}}'

async def main():
    agent = Agent(
        name="Test Operations Agent",
        instructions="You are a business operations assistant. Use the available tools to look up information requested by the user.",
        model=OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=gemini_client,
        ),
        tools=[test_find_customer],
    )

    print("Running agent with user prompt: 'Can you find customer Alice?'")
    try:
        result = await Runner.run(agent, "Can you find customer Alice?")
        print("\n=== RUN SUCCESSFUL ===")
        print(f"Final output: {result.final_output}")
        print(f"Tool calls / items: {len(result.new_items)}")
        for item in result.new_items:
            print(f"  - Item type: {type(item).__name__}: {item}")
        return True
    except Exception as e:
        print(f"\n=== RUN FAILED ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
