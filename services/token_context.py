from contextvars import ContextVar

# ContextVar to hold the user token for the current request context
token_context: ContextVar[str] = ContextVar("token_context", default="")
