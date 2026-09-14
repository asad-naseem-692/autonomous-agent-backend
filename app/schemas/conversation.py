from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1, description="User's prompt or command")

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExecutionLogResponse(BaseModel):
    id: str
    conversation_id: str
    tool_name: str
    tool_input: Any
    tool_output: Optional[Any] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationDetailResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    messages: List[MessageResponse] = []
    execution_logs: List[ExecutionLogResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SendMessageResponse(BaseModel):
    conversation_id: str
    user_message: MessageResponse
    agent_response: MessageResponse
    tool_calls: List[ExecutionLogResponse] = []
