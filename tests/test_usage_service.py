from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.usage import UsageSummary
from app.services.usage_service import UsageService


@pytest.fixture
def usage_svc():
    return UsageService()


async def test_get_summary_returns_zeroes_for_empty(usage_svc):
    mock_db = AsyncMock()
    with patch(
        "app.services.usage_service.usage_log_repo.get_summary",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = (0, 0, 0, 0)
        summary = await usage_svc.get_summary(mock_db)
        assert summary.total_input_tokens == 0
        assert summary.total_output_tokens == 0
        assert summary.total_tokens == 0
        assert summary.run_count == 0


async def test_get_summary_returns_totals(usage_svc):
    mock_db = AsyncMock()
    with patch(
        "app.services.usage_service.usage_log_repo.get_summary",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = (1000, 500, 1500, 5)
        summary = await usage_svc.get_summary(mock_db)
        assert summary.total_input_tokens == 1000
        assert summary.total_output_tokens == 500
        assert summary.total_tokens == 1500
        assert summary.run_count == 5


async def test_get_summary_by_agent_returns_per_agent(usage_svc):
    mock_db = AsyncMock()
    with patch(
        "app.services.usage_service.usage_log_repo.get_summary_by_agent",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = [("assistant", 100, 50, 150, 3)]
        result = await usage_svc.get_summary_by_agent(mock_db)
        assert "assistant" in result
        assert result["assistant"].run_count == 3


async def test_get_logs_returns_paginated(usage_svc):
    mock_db = AsyncMock()
    with patch(
        "app.services.usage_service.usage_log_repo.get_logs",
        new_callable=AsyncMock,
    ) as mock_repo:
        mock_repo.return_value = ([], 0)
        logs, total = await usage_svc.get_logs(mock_db, agent_id="test", limit=10, offset=0)
        assert total == 0
        assert len(logs) == 0
