from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ApprovalResponse(BaseModel):
    id: str
    conversation_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
