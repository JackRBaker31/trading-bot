from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsSentiment,
)
from app.orders import (
    Order,
    OrderSide,
)


class NewsTradingPolicy:
    def approve_order(
        self,
        *,
        order: Order,
        analysis: NewsAnalysis,
    ) -> bool:
        if order.side is not OrderSide.BUY:
            return True

        if (
            analysis.sentiment
            is not NewsSentiment.NEGATIVE
        ):
            return True

        if (
            analysis.impact_scope
            is not NewsImpactScope.STOCK
        ):
            return True

        matching_symbols = {
            item.upper().strip()
            for item in analysis.scope_items
        }

        return order.symbol not in matching_symbols