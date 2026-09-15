import contextvars

current_conversation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_conversation_id", default=""
)
