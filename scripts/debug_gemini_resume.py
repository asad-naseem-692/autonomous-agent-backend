import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

# Enable HTTP logging to see exact request/response
logging.basicConfig(level=logging.DEBUG)
for name in ["httpcore", "httpx", "openai"]:
    logging.getLogger(name).setLevel(logging.DEBUG)

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool

gemini_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

@function_tool(needs_approval=True)
def apply_credit(customer_id: str, amount: float, reason: str) -> str:
    """Apply credit to a customer's account."""
    print(f"  --> [EXECUTED WRITE IN TOOL] apply_credit({customer_id}, {amount})", flush=True)
    return f'{{"status": "credited", "amount": {amount}}}'

async def main():
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful business agent.",
        model=OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=gemini_client,
        ),
        tools=[apply_credit],
    )

    print("Step 1: Running agent...", flush=True)
    res = await Runner.run(agent, "Apply $10 credit to cust-123 for late shipment.")
    print(f"Interruptions: {res.interruptions}", flush=True)
    if not res.interruptions:
        return

    interruption = res.interruptions[0]
    state = res.to_state()
    state.approve(interruption)

    print("Step 2: Resuming runner...", flush=True)
    try:
        res2 = await asyncio.wait_for(Runner.run(agent, state), timeout=25.0)
        print(f"Resumed final output: {res2.final_output}", flush=True)
    except asyncio.TimeoutError:
        print("TIMEOUT on Runner.run(agent, state)!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
