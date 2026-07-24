from collections.abc import Mapping, Sequence

from app.advanced_intelligence_models import (
    MultiTimeframeAssessment,
    TimeframeAssessment,
)
from app.backtest_models import HistoricalPriceBar
from app.technical_indicators import (
    exponential_moving_average,
    relative_strength_index,
)


class MultiTimeframeService:
    WEIGHTS = {
        "MONTHLY": 0.30,
        "WEEKLY": 0.30,
        "DAILY": 0.25,
        "FOUR_HOUR": 0.10,
        "ONE_HOUR": 0.05,
    }

    MINIMUMS = {
        "MONTHLY": 24,
        "WEEKLY": 52,
        "DAILY": 200,
        "FOUR_HOUR": 120,
        "ONE_HOUR": 120,
    }

    def analyse(
        self,
        *,
        symbol: str,
        series: Mapping[
            str,
            Sequence[HistoricalPriceBar],
        ],
    ) -> MultiTimeframeAssessment:
        assessments = []

        for timeframe, weight in self.WEIGHTS.items():
            bars = sorted(
                series.get(timeframe, ()),
                key=lambda bar: bar.trading_date,
            )

            minimum = self.MINIMUMS[timeframe]
            if len(bars) < minimum:
                continue

            closes = [bar.close_price for bar in bars]
            fast_period = min(20, len(closes) // 3)
            slow_period = min(50, len(closes) // 2)

            fast = exponential_moving_average(
                values=closes,
                period=max(fast_period, 2),
            )
            slow = exponential_moving_average(
                values=closes,
                period=max(slow_period, 3),
            )
            rsi_period = min(14, len(closes) - 1)
            rsi = relative_strength_index(
                values=closes,
                period=max(rsi_period, 2),
            )

            trend_score = (
                50.0
                if closes[-1] > fast
                else 0.0
            ) + (
                30.0
                if fast > slow
                else 0.0
            )
            momentum_score = (
                20.0
                if 50 <= rsi <= 70
                else 10.0
                if 40 <= rsi < 50
                else 5.0
                if rsi > 70
                else 0.0
            )

            score = round(
                trend_score + momentum_score,
                2,
            )
            stance = (
                "BULLISH"
                if score >= 75
                else "CONSTRUCTIVE"
                if score >= 60
                else "NEUTRAL"
                if score >= 40
                else "BEARISH"
            )

            assessments.append(
                TimeframeAssessment(
                    timeframe=timeframe,
                    bar_count=len(bars),
                    score=score,
                    confidence=round(
                        min(
                            len(bars) / max(minimum, 1),
                            1.0,
                        ),
                        4,
                    ),
                    stance=stance,
                    trend=(
                        "UP"
                        if closes[-1] > fast > slow
                        else "MIXED"
                        if closes[-1] > slow
                        else "DOWN"
                    ),
                    momentum=(
                        "POSITIVE"
                        if 50 <= rsi <= 70
                        else "OVEREXTENDED"
                        if rsi > 70
                        else "WEAK"
                    ),
                    latest_close=round(
                        closes[-1],
                        6,
                    ),
                    evidence=(
                        f"Fast EMA: {fast:.4f}.",
                        f"Slow EMA: {slow:.4f}.",
                        f"RSI: {rsi:.2f}.",
                    ),
                )
            )

        if not assessments:
            raise ValueError(
                "No timeframe has enough market data."
            )

        weighted_score = 0.0
        weight_total = 0.0

        for item in assessments:
            weight = self.WEIGHTS[item.timeframe]
            weighted_score += item.score * weight
            weight_total += weight

        composite = (
            weighted_score / weight_total
            if weight_total > 0
            else 0.0
        )

        bullish = sum(
            1
            for item in assessments
            if item.stance in {"BULLISH", "CONSTRUCTIVE"}
        )
        bearish = sum(
            1
            for item in assessments
            if item.stance == "BEARISH"
        )

        conflict_penalty = (
            15.0
            if bullish > 0 and bearish > 0
            else 0.0
        )
        adjusted = max(
            composite - conflict_penalty,
            0.0,
        )

        alignment = (
            "ALIGNED_BULLISH"
            if bullish == len(assessments)
            else "ALIGNED_BEARISH"
            if bearish == len(assessments)
            else "CONFLICTED"
        )

        confidence = round(
            sum(
                item.confidence
                * self.WEIGHTS[item.timeframe]
                for item in assessments
            )
            / weight_total,
            4,
        )

        blockers = (
            (
                "Higher and lower timeframes conflict.",
            )
            if alignment == "CONFLICTED"
            else ()
        )

        return MultiTimeframeAssessment(
            symbol=symbol.upper().strip(),
            as_of_date=max(
                max(
                    bar.trading_date
                    for bar in series[item.timeframe]
                )
                for item in assessments
            ),
            composite_score=round(adjusted, 2),
            confidence=confidence,
            alignment=alignment,
            conflict_penalty=conflict_penalty,
            assessments=tuple(assessments),
            blockers=blockers,
            warnings=(
                ()
                if len(assessments) == len(self.WEIGHTS)
                else (
                    "One or more configured timeframes were unavailable.",
                )
            ),
        )
