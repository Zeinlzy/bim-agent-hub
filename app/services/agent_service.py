from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from agents import MaxTurnsExceeded, Runner, RunErrorHandlers, trace
from agents import Agent as OpenAIAgent
from openai.types.responses import ResponseTextDeltaEvent
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.factory import agent_factory
from app.agents.registry import registry
from app.config import settings
from app.core.exceptions import AgentExecutionError
from app.services.run_context import AgentRunContext
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)


def _make_error_handlers(agent_id: str, session_id: str | None) -> RunErrorHandlers:
    def on_max_turns(exc: MaxTurnsExceeded) -> str:
        logger.warning(
            "Max turns exceeded agent=%s session=%s", agent_id, session_id or "-"
        )
        return "I've reached the maximum number of turns for this conversation. Please simplify your request or start a new session."

    return RunErrorHandlers(on_max_turns_exceeded=on_max_turns)


class AgentService:
    def _build_agent(self, agent_id: str) -> OpenAIAgent:
        config = registry.get_config(agent_id)
        if not config:
            raise AgentExecutionError(f"Agent '{agent_id}' not found")
        tools = tool_registry.get_all_tools()
        return agent_factory.build(
            config, handoff_configs=registry.get_all_configs(), extra_tools=tools
        )

    def _create_context(self, agent_id: str, session_id: str | None) -> AgentRunContext:
        return AgentRunContext(
            agent_id=agent_id,
            max_turns=settings.agent_max_turns,
            timeout_seconds=settings.agent_timeout_seconds,
            session_id=session_id,
        )

    async def run(
        self,
        agent_id: str,
        messages: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> tuple[str, str | None]:
        from app.db.session import get_db_session

        async with get_db_session() as db:
            await registry.refresh(db)
            await tool_registry.refresh(db)
            agent = self._build_agent(agent_id)
            ctx = self._create_context(agent_id, session_id)
            history: list[dict[str, Any]] = []
            if session_id:
                history = await self._load_history(session_id, db)

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
                            error_handlers=_make_error_handlers(agent_id, session_id),
                        ),
                        timeout=ctx.timeout_seconds,
                    )
            except asyncio.TimeoutError:
                raise AgentExecutionError(
                    f"Agent '{agent_id}' execution timed out after {ctx.timeout_seconds}s"
                )

            content = result.final_output

            await self._record_usage(agent_id, result, ctx.elapsed_ms, session_id, db)

            if session_id:
                await self._persist_messages(agent_id, session_id, messages, content, db)

        return content, session_id

    async def run_stream(
        self,
        agent_id: str,
        messages: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        agent = self._build_agent(agent_id)
        ctx = self._create_context(agent_id, session_id)

        from app.db.session import get_db_session

        history: list[dict[str, Any]] = []
        if session_id:
            async with get_db_session() as db:
                history = await self._load_history(session_id, db)

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
                    error_handlers=_make_error_handlers(agent_id, session_id),
                )

                async for event in stream_result.stream_events():
                    if event.type == "raw_response_event" and isinstance(
                        event.data, ResponseTextDeltaEvent
                    ):
                        delta = event.data.delta or ""
                        full_content.append(delta)
                        yield delta

                async with get_db_session() as db:
                    await self._record_usage(agent_id, stream_result, ctx.elapsed_ms, session_id, db)
                    if session_id:
                        await self._persist_messages(
                            agent_id, session_id, messages, "".join(full_content), db
                        )
        except asyncio.TimeoutError:
            raise AgentExecutionError(
                f"Agent '{agent_id}' execution timed out after {ctx.timeout_seconds}s"
            )

    async def _record_usage(
        self,
        agent_id: str,
        result: Any,
        duration_ms: int | None,
        session_id: str | None,
        db: AsyncSession,
    ) -> None:
        try:
            from app.services.usage_service import usage_service

            await usage_service.record_run_usage(
                agent_id=agent_id,
                result=result,
                db=db,
                duration_ms=duration_ms,
                session_id=session_id,
            )
        except Exception:
            logger.exception(
                "Failed to record usage agent=%s session=%s",
                agent_id, session_id or "-",
            )

    async def _load_history(self, session_id: str, db: AsyncSession) -> list[dict[str, Any]]:
        from app.services.conversation_service import conversation_service

        msgs = await conversation_service.get_history(uuid.UUID(session_id), db)
        return [{"role": m.role, "content": m.content} for m in msgs]

    async def _persist_messages(
        self,
        agent_id: str,
        session_id: str,
        user_messages: list[dict[str, Any]],
        assistant_content: str,
        db: AsyncSession,
    ) -> None:
        from app.services.conversation_service import conversation_service

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
