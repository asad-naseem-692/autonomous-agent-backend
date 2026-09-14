import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.execution_log import ExecutionLog
from app.schemas.conversation import (
    MessageCreate,
    ConversationResponse,
    ConversationDetailResponse,
    SendMessageResponse,
    MessageResponse,
    ExecutionLogResponse,
)
from app.agent.runner import run_agent_turn

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all conversations for the authenticated user."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return conversations

@router.post("", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation_and_send_message(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conversation and execute the first agent turn."""
    # 1. Create conversation record
    title = payload.message.strip().split("\n")[0][:50]
    if len(payload.message.strip().split("\n")[0]) > 50:
        title += "..."

    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=title or "New Conversation",
        created_at=datetime.now(timezone.utc),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # 2. Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3. Run agent reasoning loop
    try:
        final_output, tool_logs = await run_agent_turn(
            conversation_id=conversation.id,
            user_prompt=payload.message,
            history_messages=[],
            db=db,
        )
    except Exception as exc:
        import logging as _log
        _log.getLogger(__name__).error("Agent turn failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent error: {exc}",
        )

    # 4. Save agent response message
    agent_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        content=final_output,
        created_at=datetime.now(timezone.utc),
    )
    db.add(agent_msg)
    db.commit()
    db.refresh(agent_msg)

    return SendMessageResponse(
        conversation_id=conversation.id,
        user_message=MessageResponse.model_validate(user_msg),
        agent_response=MessageResponse.model_validate(agent_msg),
        tool_calls=[ExecutionLogResponse.model_validate(t) for t in tool_logs],
    )

@router.get("/{id}", response_model=ConversationDetailResponse)
def get_conversation(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details, full message history, and execution trace of a conversation."""
    conversation = db.query(Conversation).filter(Conversation.id == id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{id}' not found",
        )

    # Scoped to owner unless admin
    if conversation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation",
        )

    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[MessageResponse.model_validate(m) for m in conversation.messages],
        execution_logs=[ExecutionLogResponse.model_validate(l) for l in conversation.execution_logs],
    )

@router.post("/{id}/messages", response_model=SendMessageResponse)
async def send_message_in_conversation(
    id: str,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a user message in an existing conversation and run the agent turn."""
    conversation = db.query(Conversation).filter(Conversation.id == id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{id}' not found",
        )

    if conversation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation",
        )

    # 1. Fetch prior messages for history
    prior_messages = (
        db.query(Message)
        .filter(Message.conversation_id == id)
        .order_by(Message.created_at.asc())
        .all()
    )

    # 2. Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 3. Run agent reasoning loop with prior context
    try:
        final_output, tool_logs = await run_agent_turn(
            conversation_id=conversation.id,
            user_prompt=payload.message,
            history_messages=prior_messages,
            db=db,
        )
    except Exception as exc:
        import logging as _log
        _log.getLogger(__name__).error("Agent turn failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent error: {exc}",
        )

    # 4. Save assistant response
    agent_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        content=final_output,
        created_at=datetime.now(timezone.utc),
    )
    db.add(agent_msg)
    db.commit()
    db.refresh(agent_msg)

    return SendMessageResponse(
        conversation_id=conversation.id,
        user_message=MessageResponse.model_validate(user_msg),
        agent_response=MessageResponse.model_validate(agent_msg),
        tool_calls=[ExecutionLogResponse.model_validate(t) for t in tool_logs],
    )
