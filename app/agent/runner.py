import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional

from openai import AsyncOpenAI, RateLimitError
from agents import Agent, OpenAIChatCompletionsModel, Runner
from agents.exceptions import ModelBehaviorError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import current_conversation_id_var
from app.models.execution_log import ExecutionLog
from app.models.message import Message
from app.tools import ALL_TOOLS

logger = logging.getLogger(__name__)

# Initialize OpenAI-compatible Gemini client
gemini_client = AsyncOpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

SYSTEM_INSTRUCTIONS = """You are the Autonomous Business Operations Agent.
Your responsibility is to assist operations staff and administrators in managing business data.
You have access to read tools to inspect system data:
1. `find_customer`: Look up a customer by name or email.
2. `get_order`: Fetch full details of an individual order by its order ID.
3. `get_order_history`: Fetch all orders belonging to a customer.
4. `calculate_balance`: Retrieve a customer's balance, unpaid orders, and net standing.

You also have access to sensitive write tools to manage customer accounts and orders:
5. `apply_credit`: Propose adding a credit amount to a customer's account. Requires customer_id, amount, and reason.
6. `process_refund`: Propose refunding an amount for an order. Requires order_id, amount, and reason.
7. `cancel_order`: Propose cancelling an order. Requires order_id and reason.
8. `update_order_status`: Propose changing an order's status (e.g. 'shipped', 'delivered', 'processing'). Requires order_id and new_status.

CRITICAL SAFETY RULES:
- Always call the relevant tool(s) to fetch or propose actual system data before answering. Do NOT make up IDs, statuses, or amounts.
- When the user asks to modify data (apply credit, refund, cancel order, update order status), ALWAYS call the appropriate write tool.
- Sensitive write actions DO NOT execute immediately; they automatically create a pending approval request that requires human confirmation.
- After calling a write tool, clearly state in your summary what action was proposed with its parameters (ID, amount, reason), and explain that the user can approve or reject it via the action card.
- Provide clear, professional, concise summaries.
"""

def create_agent() -> Agent:
    return Agent(
        name="Autonomous Business Operations Agent",
        instructions=SYSTEM_INSTRUCTIONS,
        model=OpenAIChatCompletionsModel(
            model=settings.GEMINI_CHAT_MODEL,
            openai_client=gemini_client,
        ),
        tools=ALL_TOOLS,
    )

def _parse_json_safe(val: Any) -> Any:
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return val
    return str(val)

async def run_agent_turn(
    conversation_id: str,
    user_prompt: str,
    history_messages: Optional[List[Message]] = None,
    db: Optional[Session] = None,
) -> Tuple[str, List[ExecutionLog]]:
    """Runs the agent reasoning loop for a user turn, records tool executions to execution_logs,
    and returns the final assistant summary along with the recorded tool logs.
    """
    agent = create_agent()

    # Construct prompt with conversation context if history exists
    if history_messages:
        context_lines = []
        for msg in history_messages[-6:]:  # include up to last 6 turns for context
            role_label = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{role_label}: {msg.content}")
        context_block = "\n".join(context_lines)
        full_prompt = f"Previous conversation context:\n{context_block}\n\nCurrent User Request: {user_prompt}"
    else:
        full_prompt = user_prompt

    # Set conversation id in context for tool approval creation
    current_conversation_id_var.set(conversation_id)

    logger.info("Starting agent turn for conversation %s", conversation_id)

    # Retry up to 3 times: Gemini occasionally returns an empty turn
    # (no text, no tool calls) which the SDK raises as ModelBehaviorError.
    MAX_RETRIES = 3
    last_exc: Exception | None = None
    result = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = await Runner.run(agent, full_prompt)
            break  # success
        except ModelBehaviorError as exc:
            last_exc = exc
            logger.warning(
                "ModelBehaviorError on attempt %d/%d for conv %s: %s",
                attempt, MAX_RETRIES, conversation_id, exc,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)  # 2s, 4s back-off
        except RateLimitError:
            # Quota exhausted — no point retrying, propagate immediately
            raise
        except Exception as exc:
            logger.error(
                "Unexpected error on attempt %d/%d for conv %s: %s",
                attempt, MAX_RETRIES, conversation_id, exc, exc_info=True,
            )
            raise

    if result is None:
        raise RuntimeError(
            f"Agent failed after {MAX_RETRIES} retries: {last_exc}"
        )

    final_output = result.final_output or "Action completed."

    # Extract tool calls and outputs from runner items
    tool_calls_map: Dict[str, Dict[str, Any]] = {}
    ordered_calls: List[Dict[str, Any]] = []

    for item in result.new_items:
        item_type = type(item).__name__
        raw_item = getattr(item, "raw_item", None)

        if item_type == "ToolCallItem" and raw_item is not None:
            call_id = getattr(raw_item, "call_id", None) or getattr(raw_item, "id", str(uuid.uuid4()))
            tool_name = getattr(raw_item, "name", "unknown_tool")
            args_str = getattr(raw_item, "arguments", "{}")
            call_dict = {
                "call_id": call_id,
                "tool_name": tool_name,
                "tool_input": _parse_json_safe(args_str),
                "tool_output": None,
            }
            tool_calls_map[call_id] = call_dict
            ordered_calls.append(call_dict)

        elif item_type == "ToolCallOutputItem":
            output_val = getattr(item, "output", None)
            call_id = None
            if isinstance(raw_item, dict):
                call_id = raw_item.get("call_id")
                if output_val is None:
                    output_val = raw_item.get("output")
            elif raw_item is not None:
                call_id = getattr(raw_item, "call_id", None)

            parsed_out = _parse_json_safe(output_val)
            if call_id and call_id in tool_calls_map:
                tool_calls_map[call_id]["tool_output"] = parsed_out
            elif ordered_calls and ordered_calls[-1]["tool_output"] is None:
                ordered_calls[-1]["tool_output"] = parsed_out

    # Persist execution logs in DB if session provided
    created_logs: List[ExecutionLog] = []
    if db is not None:
        for call in ordered_calls:
            is_pending = False
            if isinstance(call["tool_output"], dict) and call["tool_output"].get("status") == "pending_approval":
                is_pending = True
            elif call["tool_name"] in ["apply_credit", "process_refund", "cancel_order", "update_order_status"]:
                is_pending = True

            log_entry = ExecutionLog(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                tool_name=call["tool_name"],
                tool_input=call["tool_input"],
                tool_output=call["tool_output"],
                status="pending_approval" if is_pending else "executed",
                created_at=datetime.now(timezone.utc),
            )
            db.add(log_entry)
            created_logs.append(log_entry)
        db.commit()
        for log in created_logs:
            db.refresh(log)

    return final_output, created_logs
