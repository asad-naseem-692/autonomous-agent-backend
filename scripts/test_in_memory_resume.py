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

@function_tool(needs_approval=True)
def apply_credit(customer_id: str, amount: float, reason: str) -> str:
    """Apply credit to a customer's account."""
    print(f"  --> [EXECUTED WRITE IN TOOL] apply_credit(cust={customer_id}, amount={amount})", flush=True)
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
        print("No interruptions!")
        return

    interruption = res.interruptions[0]
    print(f"Interruption tool: {interruption.tool_name}", flush=True)

    state = res.to_state()
    print("Approving interruption on in-memory state...", flush=True)
    state.approve(interruption)

    print("Step 2: Resuming runner...", flush=True)
    res2 = await Runner.run(agent, state)
    print(f"Resumed final output: {res2.final_output}", flush=True)
    print("Done!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
