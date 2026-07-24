from collections.abc import Sequence
from datetime import date

from app.backtest_models import (
    HistoricalPriceBar,
)
from app.technical_analysis_models import (
    TechnicalAnalysis,
    TechnicalMetric,
)
from app.technical_indicators import (
    average_true_range,
    exponential_moving_average,
    relative_strength_index,
    simple_moving_average,
)


class TechnicalAnalysisService:
    MINIMUM_BAR_COUNT = 200

    def analyse(
        self,
        *,
        symbol: str,
        bars: Sequence[
            HistoricalPriceBar
        ],
    ) -> TechnicalAnalysis:
        cleaned_symbol = (
            symbol.upper().strip()
        )

        if not cleaned_symbol:
            raise ValueError(
                "Symbol is required."
            )

        ordered = sorted(
            bars,
            key=lambda bar: (
                bar.trading_date
            ),
        )

        if (
            len(ordered)
            < self.MINIMUM_BAR_COUNT
        ):
            raise ValueError(
                "At least 200 daily bars "
                "are required for technical "
                "analysis."
            )

        if any(
            bar.symbol
            != cleaned_symbol
            for bar in ordered
        ):
            raise ValueError(
                "Historical bars must all "
                "match the requested symbol."
            )

        closes = [
            bar.close_price
            for bar in ordered
        ]
        volumes = [
            float(bar.volume)
            for bar in ordered
        ]

        latest = ordered[-1]
        latest_close = (
            latest.close_price
        )

        ema20 = (
            exponential_moving_average(
                values=closes,
                period=20,
            )
        )
        ema50 = (
            exponential_moving_average(
                values=closes,
                period=50,
            )
        )
        ema200 = (
            exponential_moving_average(
                values=closes,
                period=200,
            )
        )
        rsi14 = relative_strength_index(
            values=closes,
            period=14,
        )
        atr14 = average_true_range(
            bars=list(ordered),
            period=14,
        )
        atr_percent = (
            atr14
            / latest_close
            * 100
        )
        roc20 = (
            (
                latest_close
                / closes[-21]
            )
            - 1
        ) * 100

        average_volume20 = (
            simple_moving_average(
                values=volumes,
                period=20,
            )
        )
        volume_ratio = (
            latest.volume
            / average_volume20
            if average_volume20 > 0
            else 0.0
        )

        high_52_week = max(
            bar.high_price
            for bar in ordered[-252:]
        )
        low_52_week = min(
            bar.low_price
            for bar in ordered[-252:]
        )
        range_width = (
            high_52_week
            - low_52_week
        )
        range_position = (
            (
                latest_close
                - low_52_week
            )
            / range_width
            if range_width > 0
            else 0.5
        )

        trend_metric = (
            self._trend_metric(
                latest_close=latest_close,
                ema20=ema20,
                ema50=ema50,
                ema200=ema200,
            )
        )
        momentum_metric = (
            self._momentum_metric(
                rsi14=rsi14,
                roc20=roc20,
            )
        )
        volatility_metric = (
            self._volatility_metric(
                atr_percent=atr_percent,
            )
        )
        volume_metric = (
            self._volume_metric(
                volume_ratio=volume_ratio,
                roc20=roc20,
            )
        )
        structure_metric = (
            self._structure_metric(
                range_position=(
                    range_position
                ),
                latest_close=latest_close,
                high_52_week=(
                    high_52_week
                ),
                low_52_week=(
                    low_52_week
                ),
            )
        )

        metrics = (
            trend_metric,
            momentum_metric,
            volatility_metric,
            volume_metric,
            structure_metric,
        )

        score = round(
            sum(
                metric.score
                for metric in metrics
            ),
            2,
        )

        confidence = (
            self._confidence(
                bar_count=len(ordered),
                latest_volume=(
                    latest.volume
                ),
                metric_count=len(metrics),
            )
        )

        stance = (
            "BULLISH"
            if score >= 15
            else "CONSTRUCTIVE"
            if score >= 12
            else "NEUTRAL"
            if score >= 8
            else "BEARISH"
        )

        warnings: list[str] = []

        if latest.volume == 0:
            warnings.append(
                "Latest volume is zero; "
                "volume confirmation is "
                "less reliable."
            )

        if atr_percent >= 6:
            warnings.append(
                "Daily volatility is high."
            )

        evidence = tuple(
            (
                f"{metric.label}: "
                f"{metric.display_value} "
                f"({metric.stance})."
            )
            for metric in metrics
        )

        return TechnicalAnalysis(
            symbol=cleaned_symbol,
            as_of_date=(
                latest.trading_date
            ),
            bar_count=len(ordered),
            score=score,
            maximum=20.0,
            confidence=confidence,
            stance=stance,
            trend=trend_metric.stance,
            momentum=(
                momentum_metric.stance
            ),
            volatility=(
                volatility_metric.stance
            ),
            volume_confirmation=(
                volume_metric.stance
            ),
            price_structure=(
                structure_metric.stance
            ),
            latest_close=round(
                latest_close,
                4,
            ),
            metrics=metrics,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _trend_metric(
        *,
        latest_close: float,
        ema20: float,
        ema50: float,
        ema200: float,
    ) -> TechnicalMetric:
        checks = (
            latest_close > ema20,
            ema20 > ema50,
            ema50 > ema200,
            latest_close > ema200,
        )
        passed = sum(checks)
        score = passed / 4 * 5.0

        stance = (
            "STRONG_UPTREND"
            if passed == 4
            else "UPTREND"
            if passed >= 3
            else "MIXED"
            if passed == 2
            else "DOWNTREND"
        )

        return TechnicalMetric(
            code="TREND",
            label="Trend alignment",
            value=round(
                latest_close / ema200,
                4,
            ),
            display_value=(
                f"Close {latest_close:.2f}; "
                f"EMA20 {ema20:.2f}; "
                f"EMA50 {ema50:.2f}; "
                f"EMA200 {ema200:.2f}"
            ),
            score=round(score, 2),
            maximum=5.0,
            stance=stance,
            detail=(
                f"{passed} of 4 trend "
                "alignment checks passed."
            ),
        )

    @staticmethod
    def _momentum_metric(
        *,
        rsi14: float,
        roc20: float,
    ) -> TechnicalMetric:
        rsi_score = (
            2.5
            if 55 <= rsi14 <= 70
            else 2.0
            if 50 <= rsi14 < 55
            else 1.0
            if 40 <= rsi14 < 50
            else 0.5
            if rsi14 > 70
            else 0.0
        )

        roc_score = (
            2.5
            if roc20 >= 8
            else 2.0
            if roc20 >= 3
            else 1.0
            if roc20 >= 0
            else 0.0
        )

        score = rsi_score + roc_score

        stance = (
            "STRONG"
            if score >= 4.5
            else "POSITIVE"
            if score >= 3.0
            else "MIXED"
            if score >= 1.5
            else "WEAK"
        )

        return TechnicalMetric(
            code="MOMENTUM",
            label="Momentum",
            value=round(rsi14, 2),
            display_value=(
                f"RSI14 {rsi14:.1f}; "
                f"ROC20 {roc20:+.1f}%"
            ),
            score=round(score, 2),
            maximum=5.0,
            stance=stance,
            detail=(
                "Combines RSI balance "
                "with 20-session rate "
                "of change."
            ),
        )

    @staticmethod
    def _volatility_metric(
        *,
        atr_percent: float,
    ) -> TechnicalMetric:
        if 1.0 <= atr_percent <= 3.5:
            score = 3.0
            stance = "HEALTHY"
        elif (
            0.5 <= atr_percent < 1.0
            or 3.5 < atr_percent <= 5.0
        ):
            score = 2.0
            stance = "MODERATE"
        elif atr_percent < 0.5:
            score = 1.0
            stance = "COMPRESSED"
        else:
            score = 0.5
            stance = "HIGH"

        return TechnicalMetric(
            code="VOLATILITY",
            label="Volatility",
            value=round(
                atr_percent,
                4,
            ),
            display_value=(
                f"ATR14 {atr_percent:.2f}%"
            ),
            score=score,
            maximum=3.0,
            stance=stance,
            detail=(
                "Scores ATR as a percentage "
                "of the latest close."
            ),
        )

    @staticmethod
    def _volume_metric(
        *,
        volume_ratio: float,
        roc20: float,
    ) -> TechnicalMetric:
        if (
            volume_ratio >= 1.2
            and roc20 > 0
        ):
            score = 3.0
            stance = "CONFIRMED"
        elif volume_ratio >= 1.0:
            score = 2.0
            stance = "SUPPORTIVE"
        elif volume_ratio >= 0.7:
            score = 1.0
            stance = "NORMAL"
        else:
            score = 0.5
            stance = "WEAK"

        return TechnicalMetric(
            code="VOLUME",
            label="Volume confirmation",
            value=round(
                volume_ratio,
                4,
            ),
            display_value=(
                f"{volume_ratio:.2f}x "
                "20-day average"
            ),
            score=score,
            maximum=3.0,
            stance=stance,
            detail=(
                "Compares latest volume "
                "with the 20-session average."
            ),
        )

    @staticmethod
    def _structure_metric(
        *,
        range_position: float,
        latest_close: float,
        high_52_week: float,
        low_52_week: float,
    ) -> TechnicalMetric:
        if 0.65 <= range_position <= 0.92:
            score = 4.0
            stance = "CONSTRUCTIVE"
        elif 0.50 <= range_position < 0.65:
            score = 3.0
            stance = "IMPROVING"
        elif range_position > 0.92:
            score = 2.5
            stance = "NEAR_HIGH"
        elif 0.30 <= range_position < 0.50:
            score = 1.5
            stance = "MID_RANGE"
        else:
            score = 0.5
            stance = "WEAK"

        return TechnicalMetric(
            code="PRICE_STRUCTURE",
            label="Price structure",
            value=round(
                range_position,
                4,
            ),
            display_value=(
                f"{range_position * 100:.1f}% "
                "of 52-week range"
            ),
            score=score,
            maximum=4.0,
            stance=stance,
            detail=(
                f"Latest close {latest_close:.2f}; "
                f"52-week low {low_52_week:.2f}; "
                f"high {high_52_week:.2f}."
            ),
        )

    @staticmethod
    def _confidence(
        *,
        bar_count: int,
        latest_volume: int,
        metric_count: int,
    ) -> float:
        history_score = min(
            bar_count / 252,
            1.0,
        )
        volume_score = (
            1.0
            if latest_volume > 0
            else 0.5
        )
        metric_score = min(
            metric_count / 5,
            1.0,
        )

        return round(
            0.50 * history_score
            + 0.25 * volume_score
            + 0.25 * metric_score,
            4,
        )
