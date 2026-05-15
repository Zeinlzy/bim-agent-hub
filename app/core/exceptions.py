from __future__ import annotations


class AppError(Exception):
    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str = "Internal server error"):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class AgentNotFoundError(NotFoundError):
    error_code = "agent_not_found"


class ToolNotFoundError(NotFoundError):
    error_code = "tool_not_found"


class ConversationNotFoundError(NotFoundError):
    error_code = "conversation_not_found"


class ApiKeyNotFoundError(NotFoundError):
    error_code = "api_key_not_found"


class ValidationError(AppError):
    status_code = 422
    error_code = "validation_error"


class AuthenticationError(AppError):
    status_code = 401
    error_code = "authentication_failed"


class RateLimitError(AppError):
    status_code = 429
    error_code = "rate_limit_exceeded"


class AgentExecutionError(AppError):
    status_code = 502
    error_code = "agent_execution_error"


class ToolValidationError(AppError):
    status_code = 422
    error_code = "tool_validation_error"


class ToolExecutionError(AppError):
    status_code = 502
    error_code = "tool_execution_error"
