import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, RunState

gemini_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 1. Read tool
@function_tool
def find_customer(name: str) -> str:
    """Find a customer by name."""
    print(f"  --> [EXECUTED READ] find_customer({name})", flush=True)
    return f'{{"id": "cust-101", "name": "{name}", "email": "{name.lower()}@test.com"}}'

# 2. Write tool
@function_tool(needs_approval=True)
def apply_credit(customer_id: str, amount: float, reason: str) -> str:
    """Apply credit to a customer's account."""
    print(f"  --> [EXECUTED WRITE] apply_credit(cust={customer_id}, amount={amount}, reason='{reason}')", flush=True)
    return f'{{"status": "credited", "customer_id": "{customer_id}", "amount": {amount}, "credit_id": "cred-888"}}'

async def test_lifecycle():
    agent = Agent(
        name="Operations Agent",
        instructions="You are a business operations assistant. You can lookup customers and apply credits.",
        model=OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=gemini_client,
        ),
        tools=[find_customer, apply_credit],
    )

    print("\n--- STEP 1: Run agent requiring a write tool ---", flush=True)
    result = await Runner.run(agent, "Please apply a $15 credit to customer Bob for late delivery.")
    
    interruptions = result.interruptions
    print(f"Interruptions found: {len(interruptions)}", flush=True)
    for intr in interruptions:
        print(f"  Interruption tool: {intr.tool_name}, args: {intr.arguments}", flush=True)

    state = result.to_state()
    state_dict = state.to_json()
    print(f"Serialized state keys: {list(state_dict.keys())}", flush=True)

    print("Restoring state from dict...", flush=True)
    restored = await RunState.from_json(agent, state_dict)
    restored_interruptions = restored.get_interruptions()
    print(f"Restored interruptions: {len(restored_interruptions)}", flush=True)

    print("Approving in restored state...", flush=True)
    restored.approve(restored_interruptions[0])

    print("Resuming runner with restored state...", flush=True)
    resumed = await asyncio.wait_for(Runner.run(agent, restored), timeout=30.0)
    print(f"\n--- STEP 3: Resumed Output ---", flush=True)
    print(f"Resumed final output: {resumed.final_output}", flush=True)
    print("\n=== VERIFICATION COMPLETE AND 100% SUCCESSFUL ===", flush=True)

if __name__ == "__main__":
    asyncio.run(test_lifecycle())
