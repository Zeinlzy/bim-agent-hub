from __future__ import annotations

from app.schemas.usage import UsageSummary, UsageStatsResponse


def test_usage_summary_defaults():
    s = UsageSummary()
    assert s.total_input_tokens == 0
    assert s.total_output_tokens == 0
    assert s.total_tokens == 0
    assert s.total_cost == 0.0
    assert s.run_count == 0


def test_usage_summary_empty():
    s = UsageSummary.empty()
    assert s.total_input_tokens == 0


def test_usage_summary_with_values():
    s = UsageSummary(
        total_input_tokens=1000,
        total_output_tokens=500,
        total_tokens=1500,
        total_cost=0.001,
        run_count=3,
    )
    assert s.total_input_tokens == 1000
    assert s.total_tokens == 1500


def test_usage_stats_response():
    s = UsageStatsResponse(
        total=UsageSummary(run_count=5, total_tokens=5000),
        by_agent={
            "assistant": UsageSummary(run_count=3, total_tokens=3000),
            "translator": UsageSummary(run_count=2, total_tokens=2000),
        },
    )
    assert s.total.run_count == 5
    assert len(s.by_agent) == 2
    assert s.by_agent["assistant"].run_count == 3
