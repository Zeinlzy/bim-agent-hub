from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from agents import Runner, trace
from openai.types.responses import ResponseTextDeltaEvent

from app.agents.registry import registry
from app.tools.registry import tool_registry


class AgentService:
    """Orchestrates a single agent invocation: resolve agent, run, return result."""

    async def run(
        self,
        agent_id: str,
        messages: list[dict],
    ) -> str:
        tools = tool_registry.get_all_tools()
        agent = registry.build_agent(agent_id, extra_tools=tools)

        with trace(workflow_name=agent_id, group_id=uuid.uuid4().hex):
            result = await Runner.run(agent, input=messages)

        return result.final_output

    async def run_stream(
        self,
        agent_id: str,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        tools = tool_registry.get_all_tools()
        agent = registry.build_agent(agent_id, extra_tools=tools)

        with trace(workflow_name=agent_id, group_id=uuid.uuid4().hex):
            result = Runner.run_streamed(agent, input=messages)

            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    yield event.data.delta or ""


agent_service = AgentService()
