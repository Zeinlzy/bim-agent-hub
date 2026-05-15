from __future__ import annotations

import time

from agents import RunConfig, RunHooks

import logging

logger = logging.getLogger(__name__)


class GuardrailHooks(RunHooks):
    async def on_llm_start(self, context, agent, system_prompt, input_items) -> None:
        logger.info("LLM start: agent=%s", agent.name)

    async def on_llm_end(self, context, agent, response) -> None:
        if response.usage:
            logger.info(
                "LLM end: agent=%s tokens=%d",
                agent.name,
                response.usage.total_tokens,
            )

    async def on_tool_start(self, context, agent, tool) -> None:
        logger.info("Tool call: agent=%s tool=%s", agent.name, tool.name)

    async def on_tool_end(self, context, agent, tool, result) -> None:
        logger.debug("Tool end: agent=%s tool=%s", agent.name, tool.name)


class AgentRunContext:
    def __init__(
        self,
        agent_id: str,
        max_turns: int = 25,
        timeout_seconds: int = 120,
        session_id: str | None = None,
    ):
        self.agent_id = agent_id
        self.max_turns = max_turns
        self.timeout_seconds = timeout_seconds
        self.session_id = session_id
        self.hooks = GuardrailHooks()
        self.start_time: float | None = None

    def start(self):
        self.start_time = time.monotonic()

    @property
    def elapsed_ms(self) -> int | None:
        if self.start_time is None:
            return None
        return int((time.monotonic() - self.start_time) * 1000)

    def build_run_config(self) -> RunConfig:
        return RunConfig(
            workflow_name=self.agent_id,
            trace_metadata={
                "agent_id": self.agent_id,
                "session_id": self.session_id or "",
            },
        )
