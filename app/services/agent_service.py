from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator

from agents import MaxTurnsExceeded, Runner, RunErrorHandlers, trace
from openai.types.responses import ResponseTextDeltaEvent

from app.agents.registry import registry
from app.config import settings
from app.core.exceptions import AgentExecutionError
from app.services.run_context import AgentRunContext
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)


def _make_error_handlers() -> RunErrorHandlers:
    def on_max_turns(exc: MaxTurnsExceeded) -> str:
        logger.warning("Max turns exceeded, returning fallback response")
        return "I've reached the maximum number of turns for this conversation. Please simplify your request or start a new session."

    return RunErrorHandlers(on_max_turns_exceeded=on_max_turns)


class AgentService:
    async def run(
        self,
        agent_id: str,
        messages: list[dict],
        session_id: str | None = None,
    ) -> tuple[str, str | None]:
        tools = tool_registry.get_all_tools()
        agent = registry.build_agent(agent_id, extra_tools=tools)

        ctx = AgentRunContext(
            agent_id=agent_id,
            max_turns=settings.agent_max_turns,
            timeout_seconds=settings.agent_timeout_seconds,
            session_id=session_id,
        )

        history = []
        if session_id:
            history = await self._load_history(session_id)

        all_messages = history + messages
        ctx.start()

        try:
            with trace(workflow_name=agent_id, group_id=uuid.uuid4().hex):
                result = await asyncio.wait_for(
                    Runner.run(
                        agent,
                        input=all_messages,
                        max_turns=ctx.max_turns,
                        hooks=ctx.hooks,
                        run_config=ctx.build_run_config(),
                        error_handlers=_make_error_handlers(),
                    ),
                    timeout=ctx.timeout_seconds,
                )
        except asyncio.TimeoutError:
            raise AgentExecutionError(
                f"Agent '{agent_id}' execution timed out after {ctx.timeout_seconds}s"
            )

        content = result.final_output

        await self._record_usage(agent_id, result, ctx.elapsed_ms, session_id)

        if session_id:
            await self._persist_messages(agent_id, session_id, messages, content)

        return content, session_id

    async def run_stream(
        self,
        agent_id: str,
        messages: list[dict],
        session_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        tools = tool_registry.get_all_tools()
        agent = registry.build_agent(agent_id, extra_tools=tools)

        ctx = AgentRunContext(
            agent_id=agent_id,
            max_turns=settings.agent_max_turns,
            timeout_seconds=settings.agent_timeout_seconds,
            session_id=session_id,
        )

        history = []
        if session_id:
            history = await self._load_history(session_id)

        all_messages = history + messages
        full_content: list[str] = []
        ctx.start()

        try:
            with trace(workflow_name=agent_id, group_id=uuid.uuid4().hex):
                stream_result = Runner.run_streamed(
                    agent,
                    input=all_messages,
                    max_turns=ctx.max_turns,
                    hooks=ctx.hooks,
                    run_config=ctx.build_run_config(),
                    error_handlers=_make_error_handlers(),
                )

                async for event in stream_result.stream_events():
                    if event.type == "raw_response_event" and isinstance(
                        event.data, ResponseTextDeltaEvent
                    ):
                        delta = event.data.delta or ""
                        full_content.append(delta)
                        yield delta

                await self._record_usage(agent_id, stream_result, ctx.elapsed_ms, session_id)
        except asyncio.TimeoutError:
            raise AgentExecutionError(
                f"Agent '{agent_id}' execution timed out after {ctx.timeout_seconds}s"
            )

        if session_id:
            await self._persist_messages(
                agent_id, session_id, messages, "".join(full_content)
            )

    async def _record_usage(
        self,
        agent_id: str,
        result,
        duration_ms: int | None,
        session_id: str | None,
    ) -> None:
        try:
            from app.db.session import get_db
            from app.services.usage_service import usage_service

            async for db in get_db():
                await usage_service.record_run_usage(
                    agent_id=agent_id,
                    result=result,
                    db=db,
                    duration_ms=duration_ms,
                    session_id=session_id,
                )
        except Exception:
            logger.exception("Failed to record usage for agent '%s'", agent_id)

    async def _load_history(self, session_id: str) -> list[dict]:
        from app.db.session import get_db
        from app.services.conversation_service import conversation_service

        async for db in get_db():
            msgs = await conversation_service.get_history(uuid.UUID(session_id), db)
            return [{"role": m.role, "content": m.content} for m in msgs]
        return []

    async def _persist_messages(
        self,
        agent_id: str,
        session_id: str,
        user_messages: list[dict],
        assistant_content: str,
    ) -> None:
        from app.db.session import get_db
        from app.services.conversation_service import conversation_service

        async for db in get_db():
            conv = await conversation_service.get_or_create(
                uuid.UUID(session_id), agent_id, db
            )
            for msg in user_messages:
                await conversation_service.add_message(
                    conv.id, msg.get("role", "user"), msg.get("content", ""), db
                )
            await conversation_service.add_message(
                conv.id, "assistant", assistant_content, db
            )


agent_service = AgentService()
