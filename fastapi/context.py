from contextvars import ContextVar
from typing import Optional

# Define the ContextVars with a default of None
# Naming them with a _ctx suffix is a helpful convention
username_ctx: ContextVar[Optional[str]] = ContextVar("username", default=None)
realm_ctx: ContextVar[Optional[str]] = ContextVar("realm", default=None)
apptoken_ctx: ContextVar[Optional[str]] = ContextVar("apptoken", default=None)
