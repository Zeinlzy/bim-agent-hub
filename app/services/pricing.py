from __future__ import annotations

from app.config import settings


class PricingService:
    """Calculate model usage costs from token counts.

    Uses settings.default_model_pricing as the base price list.
    Can be extended in the future to load pricing from DB.
    """

    def __init__(self):
        self._pricing = dict(settings.default_model_pricing)

    def get_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self._pricing.get(model)
        if not pricing:
            return 0.0
        input_cost, output_cost = pricing
        return (input_tokens / 1_000_000 * input_cost) + (output_tokens / 1_000_000 * output_cost)


pricing_service = PricingService()
