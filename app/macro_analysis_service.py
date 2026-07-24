from collections.abc import Mapping, Sequence
from math import sqrt
from statistics import pstdev

from app.backtest_models import HistoricalPriceBar
from app.macro_analysis_models import MacroAnalysis, MacroMetric
from app.technical_indicators import exponential_moving_average


class MacroAnalysisService:
    REQUIRED_SYMBOLS = ("SPY", "QQQ", "TLT")
    MINIMUM_BAR_COUNT = 200

    def analyse(
        self,
        *,
        series: Mapping[str, Sequence[HistoricalPriceBar]],
    ) -> MacroAnalysis:
        normalised = {
            symbol.upper().strip(): sorted(
                bars,
                key=lambda bar: bar.trading_date,
            )
            for symbol, bars in series.items()
        }

        missing = [
            symbol for symbol in self.REQUIRED_SYMBOLS
            if symbol not in normalised
        ]
        if missing:
            raise ValueError(
                "Missing macro series: " + ", ".join(missing) + "."
            )

        for symbol in self.REQUIRED_SYMBOLS:
            bars = normalised[symbol]
            if len(bars) < self.MINIMUM_BAR_COUNT:
                raise ValueError(
                    f"{symbol} requires at least 200 daily bars."
                )
            if any(bar.symbol != symbol for bar in bars):
                raise ValueError(
                    f"{symbol} bars contain a mismatched symbol."
                )

        common_date = min(
            normalised[symbol][-1].trading_date
            for symbol in self.REQUIRED_SYMBOLS
        )
        aligned = {
            symbol: [
                bar for bar in normalised[symbol]
                if bar.trading_date <= common_date
            ]
            for symbol in self.REQUIRED_SYMBOLS
        }

        broad_market = self._broad_market_metric(bars=aligned["SPY"])
        growth = self._growth_leadership_metric(
            spy=aligned["SPY"],
            qqq=aligned["QQQ"],
        )
        rates = self._rate_pressure_metric(bars=aligned["TLT"])
        volatility = self._volatility_metric(bars=aligned["SPY"])
        freshness = MacroMetric(
            code="FRESHNESS",
            label="Data freshness",
            value=0.0,
            display_value=f"Latest aligned date {common_date.isoformat()}",
            score=1.0,
            maximum=1.0,
            stance="FRESH",
            detail=(
                "All macro proxy series were aligned to a common "
                "latest trading date."
            ),
        )

        metrics = (broad_market, growth, rates, volatility, freshness)
        score = round(sum(item.score for item in metrics), 2)
        regime = (
            "RISK_ON" if score >= 7.5
            else "CONSTRUCTIVE" if score >= 6.0
            else "MIXED" if score >= 4.0
            else "RISK_OFF"
        )
        stance = (
            "SUPPORTIVE" if score >= 7.0
            else "NEUTRAL" if score >= 4.5
            else "HEADWIND"
        )
        confidence = self._confidence(series=aligned)

        warnings = []
        if volatility.stance == "HIGH":
            warnings.append("Broad-market realised volatility is high.")
        if rates.stance == "PRESSURE":
            warnings.append(
                "Long-duration bond trend indicates rate pressure."
            )

        return MacroAnalysis(
            as_of_date=common_date,
            score=score,
            maximum=10.0,
            confidence=confidence,
            stance=stance,
            regime=regime,
            broad_market_trend=broad_market.stance,
            growth_leadership=growth.stance,
            rate_pressure=rates.stance,
            volatility_regime=volatility.stance,
            metrics=metrics,
            evidence=tuple(
                f"{item.label}: {item.display_value} ({item.stance})."
                for item in metrics
            ),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _broad_market_metric(
        *,
        bars: Sequence[HistoricalPriceBar],
    ) -> MacroMetric:
        closes = [bar.close_price for bar in bars]
        latest = closes[-1]
        ema50 = exponential_moving_average(values=closes, period=50)
        ema200 = exponential_moving_average(values=closes, period=200)
        checks = (latest > ema50, ema50 > ema200, latest > ema200)
        passed = sum(checks)
        score = passed / 3 * 3.0
        stance = (
            "STRONG_UPTREND" if passed == 3
            else "UPTREND" if passed == 2
            else "MIXED" if passed == 1
            else "DOWNTREND"
        )
        return MacroMetric(
            code="BROAD_MARKET",
            label="Broad-market trend",
            value=round(latest / ema200, 4),
            display_value=(
                f"SPY {latest:.2f}; EMA50 {ema50:.2f}; "
                f"EMA200 {ema200:.2f}"
            ),
            score=round(score, 2),
            maximum=3.0,
            stance=stance,
            detail=f"{passed} of 3 SPY trend checks passed.",
        )

    @staticmethod
    def _growth_leadership_metric(
        *,
        spy: Sequence[HistoricalPriceBar],
        qqq: Sequence[HistoricalPriceBar],
    ) -> MacroMetric:
        spy_return = spy[-1].close_price / spy[-64].close_price - 1
        qqq_return = qqq[-1].close_price / qqq[-64].close_price - 1
        relative = qqq_return - spy_return
        if relative >= 0.03:
            score, stance = 2.0, "LEADING"
        elif relative >= 0.0:
            score, stance = 1.5, "SUPPORTIVE"
        elif relative >= -0.03:
            score, stance = 0.75, "LAGGING"
        else:
            score, stance = 0.0, "WEAK"
        return MacroMetric(
            code="GROWTH_LEADERSHIP",
            label="Growth leadership",
            value=round(relative * 100, 4),
            display_value=(
                "QQQ minus SPY 63-session return "
                f"{relative * 100:+.2f}%"
            ),
            score=score,
            maximum=2.0,
            stance=stance,
            detail=(
                "Uses QQQ relative performance versus SPY as a "
                "liquid risk-appetite proxy."
            ),
        )

    @staticmethod
    def _rate_pressure_metric(
        *,
        bars: Sequence[HistoricalPriceBar],
    ) -> MacroMetric:
        closes = [bar.close_price for bar in bars]
        latest = closes[-1]
        ema50 = exponential_moving_average(values=closes, period=50)
        return_63 = latest / closes[-64] - 1
        if latest > ema50 and return_63 >= 0:
            score, stance = 2.0, "EASING"
        elif latest > ema50:
            score, stance = 1.5, "STABILISING"
        elif return_63 >= -0.03:
            score, stance = 0.75, "MODERATE"
        else:
            score, stance = 0.0, "PRESSURE"
        return MacroMetric(
            code="RATE_PRESSURE",
            label="Rate pressure",
            value=round(return_63 * 100, 4),
            display_value=f"TLT 63-session return {return_63 * 100:+.2f}%",
            score=score,
            maximum=2.0,
            stance=stance,
            detail=(
                "A strengthening long-duration bond proxy is treated "
                "as easing rate pressure."
            ),
        )

    @staticmethod
    def _volatility_metric(
        *,
        bars: Sequence[HistoricalPriceBar],
    ) -> MacroMetric:
        closes = [bar.close_price for bar in bars[-22:]]
        returns = [
            closes[index] / closes[index - 1] - 1
            for index in range(1, len(closes))
        ]
        realised = pstdev(returns) * sqrt(252) * 100
        if realised <= 15:
            score, stance = 2.0, "CALM"
        elif realised <= 22:
            score, stance = 1.5, "NORMAL"
        elif realised <= 30:
            score, stance = 0.75, "ELEVATED"
        else:
            score, stance = 0.0, "HIGH"
        return MacroMetric(
            code="VOLATILITY",
            label="Volatility regime",
            value=round(realised, 4),
            display_value=(
                "SPY 21-session annualised volatility "
                f"{realised:.1f}%"
            ),
            score=score,
            maximum=2.0,
            stance=stance,
            detail=(
                "Uses realised broad-market volatility rather than "
                "an unverified volatility-index value."
            ),
        )

    @staticmethod
    def _confidence(
        *,
        series: Mapping[str, Sequence[HistoricalPriceBar]],
    ) -> float:
        history = min(
            min(len(bars) for bars in series.values()) / 252,
            1.0,
        )
        volume = (
            sum(1 for bars in series.values() if bars[-1].volume > 0)
            / len(series)
        )
        return round(0.8 * history + 0.2 * volume, 4)
