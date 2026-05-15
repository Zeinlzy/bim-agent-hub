from __future__ import annotations

from app.services.pricing import PricingService, pricing_service


def test_get_cost_known_model():
    cost = pricing_service.get_cost("deepseek-chat", 1_000_000, 1_000_000)
    assert cost == 0.27 + 1.10


def test_get_cost_known_model_partial():
    cost = pricing_service.get_cost("gpt-4o-mini", 1000, 500)
    assert cost == (1000 / 1_000_000 * 0.15) + (500 / 1_000_000 * 0.60)


def test_get_cost_unknown_model_returns_zero():
    cost = pricing_service.get_cost("unknown-model", 1000, 1000)
    assert cost == 0.0


def test_get_cost_zero_tokens():
    cost = pricing_service.get_cost("gpt-4o", 0, 0)
    assert cost == 0.0


def test_pricing_service_uses_config_defaults():
    svc = PricingService()
    assert "deepseek-chat" in svc._pricing
    assert svc._pricing["deepseek-chat"] == (0.27, 1.10)
