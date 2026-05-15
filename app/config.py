from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    port: int = Field(8000, ge=1, le=65535)
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentapi"
    database_pool_size: int = Field(10, ge=1)
    database_max_overflow: int = Field(20, ge=0)
    run_migrations_on_startup: bool = True

    # Auth
    auth_enabled: bool = False
    admin_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_requests_per_minute: int = Field(60, ge=1)

    # Execution guardrails
    agent_max_turns: int = Field(25, ge=1)
    agent_timeout_seconds: int = Field(120, ge=1)

    # In-process cache TTL for multi-worker deployments.
    # Registries reload from DB when a read occurs after this many seconds.
    # Set to 0 to disable caching (always read from DB).
    cache_ttl_seconds: int = Field(30, ge=0)

    # Tool security
    # Static AST validation for dynamically-submitted tool code
    tool_validation_enabled: bool = True
    # When True, dynamic (user-submitted) tool code is executed via exec() in-process.
    # When False (default), only builtin tools (get_current_time, echo) are allowed.
    # WARNING: this is NOT subprocess isolation. Only enable if you trust all users
    # who can call POST /v1/tools, or run inside a container/VM-level sandbox.
    tool_dynamic_exec_enabled: bool = False

    # Default model pricing (input_cost_per_1m, output_cost_per_1m)
    # Used as startup defaults; can be overridden at runtime via PricingService
    default_model_pricing: dict[str, tuple[float, float]] = {
        "deepseek-chat": (0.27, 1.10),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
    }

    # CORS
    cors_allow_origins: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
