from __future__ import annotations

import json
import math
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any


class FeatureContributionService:
    """Read-only analytics over persisted opportunity-ranking components.

    The service never changes ranking weights or execution behaviour. It joins
    persisted ranking snapshots to realised forward outcomes and reports how
    each score component behaved historically.
    """

    def __init__(self, *, database_path: str = "data/application.db") -> None:
        self._database_path = database_path

    def generate(self, *, days: int = 90, horizon_days: int = 1) -> dict[str, Any]:
        if days not in {7, 30, 90, 365}:
            raise ValueError("Feature contribution days must be 7, 30, 90, or 365.")
        if horizon_days not in {1, 5, 20}:
            raise ValueError("Feature contribution horizon must be 1, 5, or 20 days.")

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        rows = self._load_rows(start=start, horizon_days=horizon_days)
        latest = self._load_latest_vectors(limit=20)
        features = self._aggregate(rows)
        measured = len({int(row["outcome_id"]) for row in rows if row["outcome_id"] is not None})

        return {
            "generated_at": now.isoformat(),
            "period": {"days": days, "start": start.isoformat(), "end": now.isoformat()},
            "horizon_days": horizon_days,
            "status": "EVIDENCE_BUILDING" if measured < 150 else "REVIEW_READY",
            "trading_impact": "NONE",
            "automatic_weight_changes": False,
            "summary": {
                "tracked_snapshot_count": len({int(row["snapshot_id"]) for row in rows}),
                "measured_outcome_count": measured,
                "feature_count": len(features),
                "positive_feature_count": sum(1 for item in features if (item["average_alpha_percent"] or 0) > 0),
                "strongest_feature": features[0]["label"] if features else None,
                "weakest_feature": features[-1]["label"] if features else None,
            },
            "features": features,
            "latest_vectors": latest,
            "recommendations": self._recommendations(features, measured),
            "methodology": {
                "source": "Persisted opportunity ranking snapshots joined to forward outcomes",
                "contribution_definition": "Weighted points contributed to the final opportunity score",
                "outcome_definition": f"Realised {horizon_days}-day return and alpha versus benchmark",
                "minimum_serious_review_sample": 150,
                "read_only": True,
            },
        }

    def _load_rows(self, *, start: datetime, horizon_days: int) -> list[sqlite3.Row]:
        if not Path(self._database_path).exists():
            return []
        with sqlite3.connect(self._database_path) as connection:
            connection.row_factory = sqlite3.Row
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "opportunity_ranking_snapshots" not in tables:
                return []
            has_outcomes = "opportunity_ranking_forward_outcomes" in tables
            if has_outcomes:
                query = """
                    SELECT s.snapshot_id, s.captured_at, s.symbol, s.rank,
                           s.opportunity_score, s.component_values_json,
                           s.component_labels_json,
                           o.outcome_id, o.return_percent, o.alpha_percent,
                           o.maximum_drawdown_percent
                    FROM opportunity_ranking_snapshots s
                    LEFT JOIN opportunity_ranking_forward_outcomes o
                      ON o.snapshot_id = s.snapshot_id AND o.horizon_days = ?
                    WHERE s.captured_at >= ?
                    ORDER BY s.captured_at ASC, s.snapshot_id ASC
                """
                return connection.execute(query, (horizon_days, start.isoformat())).fetchall()
            return connection.execute(
                """
                SELECT snapshot_id, captured_at, symbol, rank, opportunity_score,
                       component_values_json, component_labels_json,
                       NULL AS outcome_id, NULL AS return_percent,
                       NULL AS alpha_percent, NULL AS maximum_drawdown_percent
                FROM opportunity_ranking_snapshots
                WHERE captured_at >= ?
                ORDER BY captured_at ASC, snapshot_id ASC
                """,
                (start.isoformat(),),
            ).fetchall()

    def _load_latest_vectors(self, *, limit: int) -> list[dict[str, Any]]:
        if not Path(self._database_path).exists():
            return []
        with sqlite3.connect(self._database_path) as connection:
            connection.row_factory = sqlite3.Row
            try:
                rows = connection.execute(
                    """
                    SELECT snapshot_id, captured_at, symbol, rank,
                           opportunity_score, component_values_json,
                           component_labels_json
                    FROM opportunity_ranking_snapshots
                    ORDER BY captured_at DESC, snapshot_id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            except sqlite3.Error:
                return []
        result = []
        for row in rows:
            values = self._json_dict(row["component_values_json"])
            labels = self._json_dict(row["component_labels_json"])
            components = [
                {"code": code, "label": str(labels.get(code, code.replace("_", " ").title())), "value": round(float(value), 4)}
                for code, value in values.items()
                if self._number(value) is not None
            ]
            components.sort(key=lambda item: abs(item["value"]), reverse=True)
            result.append({
                "snapshot_id": int(row["snapshot_id"]),
                "captured_at": str(row["captured_at"]),
                "symbol": str(row["symbol"]),
                "rank": int(row["rank"]),
                "opportunity_score": float(row["opportunity_score"]),
                "components": components,
            })
        return result

    def _aggregate(self, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "label": "", "all_values": [], "measured_values": [],
            "returns": [], "alphas": [], "drawdowns": [],
        })
        for row in rows:
            values = self._json_dict(row["component_values_json"])
            labels = self._json_dict(row["component_labels_json"])
            for code, raw_value in values.items():
                value = self._number(raw_value)
                if value is None:
                    continue
                bucket = grouped[code]
                bucket["label"] = str(labels.get(code, code.replace("_", " ").title()))
                bucket["all_values"].append(value)
                if row["outcome_id"] is not None:
                    bucket["measured_values"].append(value)
                    bucket["returns"].append(float(row["return_percent"]))
                    bucket["alphas"].append(float(row["alpha_percent"]))
                    bucket["drawdowns"].append(float(row["maximum_drawdown_percent"]))

        result = []
        for code, data in grouped.items():
            sample = len(data["returns"])
            positive = sum(1 for value in data["returns"] if value > 0)
            result.append({
                "code": code,
                "label": data["label"],
                "snapshot_count": len(data["all_values"]),
                "measured_count": sample,
                "average_contribution": self._round_mean(data["all_values"]),
                "median_contribution": round(median(data["all_values"]), 4) if data["all_values"] else None,
                "directional_success_percent": round(positive / sample * 100, 2) if sample else None,
                "average_return_percent": self._round_mean(data["returns"]),
                "average_alpha_percent": self._round_mean(data["alphas"]),
                "average_drawdown_percent": self._round_mean(data["drawdowns"]),
                "contribution_return_correlation": self._correlation(data["measured_values"], data["returns"]),
                "evidence": "LIMITED" if sample < 30 else "MODERATE" if sample < 150 else "STRONG",
            })
        result.sort(key=lambda item: ((item["average_alpha_percent"] if item["average_alpha_percent"] is not None else -999), item["measured_count"]), reverse=True)
        return result

    @staticmethod
    def _recommendations(features: list[dict[str, Any]], measured: int) -> list[dict[str, Any]]:
        if measured < 150:
            return [{
                "code": "FEATURE-EVIDENCE-001",
                "title": "Continue unchanged contribution collection",
                "reason": f"Only {measured} realised outcomes are available; 150 are required before serious weight review.",
                "automatic_change": False,
                "risk": "LOW",
            }]
        recommendations = []
        for item in features:
            if item["measured_count"] >= 50 and item["average_alpha_percent"] is not None and item["average_alpha_percent"] < 0:
                recommendations.append({
                    "code": f"FEATURE-REVIEW-{item['code']}",
                    "title": f"Review {item['label']} contribution",
                    "reason": f"The feature is associated with {item['average_alpha_percent']:.2f}% average alpha across {item['measured_count']} measured outcomes.",
                    "automatic_change": False,
                    "risk": "MEDIUM",
                })
        return recommendations[:5]

    @staticmethod
    def _json_dict(value: Any) -> dict[str, Any]:
        try:
            parsed = json.loads(str(value))
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None

    @staticmethod
    def _round_mean(values: list[float]) -> float | None:
        return round(mean(values), 4) if values else None

    @staticmethod
    def _correlation(xs: list[float], ys: list[float]) -> float | None:
        if len(xs) < 3 or len(xs) != len(ys):
            return None
        x_mean, y_mean = mean(xs), mean(ys)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        x_den = sum((x - x_mean) ** 2 for x in xs)
        y_den = sum((y - y_mean) ** 2 for y in ys)
        denominator = math.sqrt(x_den * y_den)
        return None if denominator == 0 else round(numerator / denominator, 4)
