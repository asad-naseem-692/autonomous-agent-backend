import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional

from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.execution_log import ExecutionLog
from app.models.message import Message
from app.tools import READ_TOOLS

logger = logging.getLogger(__name__)

# Initialize OpenAI-compatible Gemini client
gemini_client = AsyncOpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

SYSTEM_INSTRUCTIONS = """You are the Autonomous Business Operations Agent.
Your responsibility is to assist operations staff and administrators in managing business data.
You have access to read tools to find customers, look up order details, inspect customer order history, and calculate account balances and dues:
1. `find_customer`: Look up a customer by name or email.
2. `get_order`: Fetch full details of an individual order by its order ID.
3. `get_order_history`: Fetch all orders belonging to a customer.
4. `calculate_balance`: Retrieve a customer's balance, unpaid orders, and net standing.

Always call the relevant tool(s) to fetch actual system data before answering. Do NOT make up IDs, statuses, or amounts.
After receiving tool results, provide a clear, professional, concise summary answering the user's request. Include key details (IDs, amounts, statuses, and dates where relevant).
"""

def create_agent() -> Agent:
    return Agent(
        name="Autonomous Business Operations Agent",
        instructions=SYSTEM_INSTRUCTIONS,
        model=OpenAIChatCompletionsModel(
            model=settings.GEMINI_CHAT_MODEL,
            openai_client=gemini_client,
        ),
        tools=READ_TOOLS,
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

    logger.info("Starting agent turn for conversation %s", conversation_id)
    result = await Runner.run(agent, full_prompt)
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
            log_entry = ExecutionLog(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                tool_name=call["tool_name"],
                tool_input=call["tool_input"],
                tool_output=call["tool_output"],
                status="executed",
                created_at=datetime.now(timezone.utc),
            )
            db.add(log_entry)
            created_logs.append(log_entry)
        db.commit()
        for log in created_logs:
            db.refresh(log)

    return final_output, created_logs
