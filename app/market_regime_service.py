from collections.abc import Mapping, Sequence
from math import sqrt
from statistics import pstdev

from app.advanced_intelligence_models import (
    MarketRegimeAssessment,
)
from app.backtest_models import HistoricalPriceBar
from app.technical_indicators import (
    exponential_moving_average,
)


class MarketRegimeService:
    REQUIRED_SYMBOLS = ("SPY", "QQQ", "TLT")
    MINIMUM_BAR_COUNT = 200

    def analyse(
        self,
        *,
        series: Mapping[
            str,
            Sequence[HistoricalPriceBar],
        ],
    ) -> MarketRegimeAssessment:
        normalised = {
            symbol.upper().strip(): sorted(
                bars,
                key=lambda bar: bar.trading_date,
            )
            for symbol, bars in series.items()
        }

        for symbol in self.REQUIRED_SYMBOLS:
            if symbol not in normalised:
                raise ValueError(
                    f"Missing regime series: {symbol}."
                )
            if len(normalised[symbol]) < self.MINIMUM_BAR_COUNT:
                raise ValueError(
                    f"{symbol} requires at least 200 bars."
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

        spy = aligned["SPY"]
        qqq = aligned["QQQ"]
        tlt = aligned["TLT"]

        spy_closes = [bar.close_price for bar in spy]
        qqq_closes = [bar.close_price for bar in qqq]
        tlt_closes = [bar.close_price for bar in tlt]

        spy_50 = exponential_moving_average(
            values=spy_closes,
            period=50,
        )
        spy_200 = exponential_moving_average(
            values=spy_closes,
            period=200,
        )

        trend_checks = (
            spy_closes[-1] > spy_50,
            spy_50 > spy_200,
            spy_closes[-1] > spy_200,
        )
        trend_count = sum(trend_checks)

        returns = [
            spy_closes[index] / spy_closes[index - 1] - 1
            for index in range(
                len(spy_closes) - 21,
                len(spy_closes),
            )
        ]
        realised_volatility = (
            pstdev(returns) * sqrt(252) * 100
        )

        qqq_relative = (
            qqq_closes[-1] / qqq_closes[-64]
            - spy_closes[-1] / spy_closes[-64]
        )
        tlt_return = (
            tlt_closes[-1] / tlt_closes[-64] - 1
        )

        trend_state = (
            "TRENDING_UP"
            if trend_count == 3
            else "MIXED"
            if trend_count in (1, 2)
            else "TRENDING_DOWN"
        )

        volatility_state = (
            "LOW"
            if realised_volatility <= 15
            else "NORMAL"
            if realised_volatility <= 22
            else "HIGH"
            if realised_volatility <= 30
            else "EXTREME"
        )

        risk_state = (
            "RISK_ON"
            if qqq_relative >= 0 and tlt_return >= -0.03
            else "MIXED"
            if qqq_relative >= -0.03
            else "RISK_OFF"
        )

        score = 0.0
        score += trend_count / 3 * 45.0
        score += (
            30.0
            if risk_state == "RISK_ON"
            else 15.0
            if risk_state == "MIXED"
            else 0.0
        )
        score += (
            25.0
            if volatility_state in {"LOW", "NORMAL"}
            else 10.0
            if volatility_state == "HIGH"
            else 0.0
        )
        score = round(score, 2)

        regime = (
            "BULL"
            if score >= 75
            else "CONSTRUCTIVE"
            if score >= 60
            else "SIDEWAYS"
            if score >= 40
            else "BEAR"
        )

        buy_threshold = {
            "BULL": 75.0,
            "CONSTRUCTIVE": 80.0,
            "SIDEWAYS": 85.0,
            "BEAR": 90.0,
        }[regime]

        position_multiplier = {
            "BULL": 1.0,
            "CONSTRUCTIVE": 0.85,
            "SIDEWAYS": 0.60,
            "BEAR": 0.35,
        }[regime]

        if volatility_state == "HIGH":
            position_multiplier *= 0.75
        elif volatility_state == "EXTREME":
            position_multiplier *= 0.50

        confidence = round(
            min(
                min(
                    len(aligned[symbol])
                    for symbol in self.REQUIRED_SYMBOLS
                ) / 252,
                1.0,
            ),
            4,
        )

        warnings = []
        if volatility_state in {"HIGH", "EXTREME"}:
            warnings.append(
                "Elevated volatility requires stronger confirmation."
            )
        if regime == "BEAR":
            warnings.append(
                "Bear regime applies the highest BUY threshold."
            )

        return MarketRegimeAssessment(
            as_of_date=common_date,
            regime=regime,
            trend_state=trend_state,
            volatility_state=volatility_state,
            risk_state=risk_state,
            score=score,
            confidence=confidence,
            buy_threshold=buy_threshold,
            position_multiplier=round(
                position_multiplier,
                4,
            ),
            evidence=(
                f"SPY trend checks passed: {trend_count}/3.",
                (
                    "SPY annualised 21-session volatility: "
                    f"{realised_volatility:.1f}%."
                ),
                (
                    "QQQ relative 63-session performance: "
                    f"{qqq_relative * 100:+.2f}%."
                ),
                (
                    "TLT 63-session return: "
                    f"{tlt_return * 100:+.2f}%."
                ),
            ),
            warnings=tuple(warnings),
        )
