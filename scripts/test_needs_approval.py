import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool

gemini_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Read tool (needs_approval=False)
@function_tool
def find_customer(name: str) -> str:
    """Find a customer by name."""
    print(f"--> [READ TOOL] find_customer({name})")
    return f'{{"id": "cust-999", "name": "{name}", "email": "{name.lower()}@test.com"}}'

# Write tool (needs_approval=True)
@function_tool(needs_approval=True)
def apply_credit(customer_id: str, amount: float, reason: str) -> str:
    """Apply credit to a customer's account."""
    print(f"--> [WRITE TOOL CALLED] apply_credit(cust={customer_id}, amount={amount}, reason={reason})")
    return f'{{"status": "credited", "customer_id": "{customer_id}", "amount": {amount}}}'

async def test_builtin_approval():
    print("=== TESTING BUILT-IN SDK needs_approval=True ===")
    agent = Agent(
        name="Operations Agent",
        instructions="You are a business operations assistant. You can lookup customers and apply credits.",
        model=OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=gemini_client,
        ),
        tools=[find_customer, apply_credit],
    )

    result = await Runner.run(agent, "Apply a $25 credit to customer Alice for inconvenience.")
    print(f"Result final_output: {result.final_output}")
    print(f"Result items count: {len(result.new_items)}")
    for item in result.new_items:
        print(f"  Item type: {type(item).__name__}: {item}")

if __name__ == "__main__":
    asyncio.run(test_builtin_approval())
