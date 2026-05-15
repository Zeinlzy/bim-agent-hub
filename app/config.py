from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    port: int = 8000
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentapi"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    run_migrations_on_startup: bool = True

    # Auth
    auth_enabled: bool = False
    admin_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_requests_per_minute: int = 60

    # Execution guardrails
    agent_max_turns: int = 25
    agent_timeout_seconds: int = 120

    # Tool security
    tool_validation_enabled: bool = True
    tool_subprocess_enabled: bool = False

    # Model pricing (input_cost_per_1m, output_cost_per_1m)
    model_pricing: dict[str, tuple[float, float]] = {
        "deepseek-chat": (0.27, 1.10),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
    }

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
