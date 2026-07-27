from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class ReviewWindow:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("Review dates must be timezone-aware.")
        if self.end <= self.start:
            raise ValueError("Review end must follow review start.")


# Deliberately local and deterministic. Unknown symbols remain "Other" rather
# than making an external metadata request while producing a review.
SECTOR_SYMBOLS: dict[str, set[str]] = {
    "Technology": {"AAPL", "ADBE", "AMAT", "AMD", "ANET", "AVGO", "CRM", "CRWD", "CSCO", "GOOGL", "INTC", "KLAC", "META", "MSFT", "MU", "NVDA", "ORCL", "PANW", "PLTR", "QCOM", "SNOW", "TXN", "XLK", "SMH"},
    "Communication Services": {"DIS", "NFLX", "ROKU", "T", "TMUS", "VZ"},
    "Consumer Discretionary": {"ABNB", "AMZN", "BKNG", "HD", "LOW", "MCD", "NKE", "SBUX", "TSLA"},
    "Consumer Staples": {"CL", "COST", "KMB", "KO", "MDLZ", "MO", "PEP", "PG", "PM", "WMT"},
    "Financials": {"AXP", "BAC", "BLK", "GS", "JPM", "MA", "MS", "SCHW", "V", "WFC", "XLF"},
    "Healthcare": {"ABBV", "ABT", "DHR", "ISRG", "JNJ", "LLY", "MRK", "PFE", "TMO", "UNH", "XLV"},
    "Industrials": {"CAT", "DE", "ETN", "FDX", "GE", "HON", "LMT", "PH", "RTX", "UPS"},
    "Energy": {"COP", "CVX", "EOG", "MPC", "OXY", "PSX", "SLB", "XLE", "XOM"},
    "Utilities": {"AEP", "DUK", "NEE", "SO"},
    "Materials": {"APD", "FCX", "LIN", "NEM", "SHW"},
    "Real Estate": {"AMT", "EQIX", "PLD"},
    "Broad Market": {"IWM", "QQQ", "SPY"},
}

SYMBOL_TO_SECTOR = {
    symbol: sector
    for sector, symbols in SECTOR_SYMBOLS.items()
    for symbol in symbols
}


class PerformanceReviewService:
    def __init__(self, *, database_path: str = "data/application.db") -> None:
        cleaned = database_path.strip()
        if not cleaned:
            raise ValueError("Database path is required.")
        self._database_path = Path(cleaned)

    def generate(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, Any]:
        end_utc = self._utc(end or datetime.now(timezone.utc))
        start_utc = self._utc(start or (end_utc - timedelta(days=3)))
        window = ReviewWindow(start=start_utc, end=end_utc)

        with self._connect() as connection:
            jobs = self._rows_between(connection, table="jobs", timestamp_column="created_at", window=window)
            runs = self._rows_between(connection, table="run_history", timestamp_column="started_at", window=window)
            decisions = self._rows_between(connection, table="shadow_decisions", timestamp_column="created_at", window=window)
            memories = self._rows_between(connection, table="decision_memory", timestamp_column="captured_at", window=window)
            snapshots = self._rows_between(connection, table="copilot_decision_snapshots", timestamp_column="captured_at", window=window)
            outcomes = self._rows_between(connection, table="decision_outcomes", timestamp_column="observed_at", window=window)

        job_summary = self._job_summary(jobs)
        research_summary = self._research_summary(runs, jobs)
        outcome_index = self._outcomes_by_decision(outcomes)
        decision_summary = self._decision_summary(decisions, memories)
        outcome_summary = self._outcome_summary(outcomes, jobs)
        confidence_summary = self._confidence_summary(snapshots, decisions, outcome_index)
        decision_summary["opportunities_seen"] = outcome_summary["opportunities_seen"]
        decision_summary["decisions_skipped"] = outcome_summary["decisions_skipped"]
        sector_analytics = self._sector_analytics(decisions, outcome_index)
        symbol_analytics = self._symbol_analytics(decisions, outcome_index)
        blocker_analytics = self._blocker_analytics(decisions, memories)
        trends = self._trends(window, jobs, runs, decisions, outcomes)
        maturity = self._maturity(snapshots, decision_summary, outcome_summary, job_summary)
        insights = self._insights(
            job_summary=job_summary,
            research_summary=research_summary,
            decision_summary=decision_summary,
            outcome_summary=outcome_summary,
            confidence_summary=confidence_summary,
            sector_analytics=sector_analytics,
            blocker_analytics=blocker_analytics,
        )

        result: dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
                "hours": round((window.end - window.start).total_seconds() / 3600, 2),
            },
            "executive_summary": self._executive_summary(
                job_summary=job_summary,
                research_summary=research_summary,
                decision_summary=decision_summary,
                outcome_summary=outcome_summary,
                sector_analytics=sector_analytics,
            ),
            "system_health": job_summary,
            "research_activity": research_summary,
            "decision_intelligence": decision_summary,
            "shadow_performance": outcome_summary,
            "confidence_calibration": confidence_summary,
            "sector_analytics": sector_analytics,
            "symbol_analytics": symbol_analytics,
            "blocker_analytics": blocker_analytics,
            "trends": trends,
            "maturity": maturity,
            "insights": insights,
        }
        result["markdown"] = self.to_markdown(result)
        return result

    def to_markdown(self, review: dict[str, Any]) -> str:
        period = review["period"]
        health = review["system_health"]
        research = review["research_activity"]
        decisions = review["decision_intelligence"]
        performance = review["shadow_performance"]
        confidence = review["confidence_calibration"]
        maturity = review["maturity"]

        lines = [
            "# KAIRO Performance Intelligence Review",
            "",
            f"**Period:** {period['start']} to {period['end']}",
            f"**Generated:** {review['generated_at']}",
            "",
            "## Executive Summary",
            "",
            review["executive_summary"],
            "",
            "## Platform Maturity",
            "",
            f"- Maturity score: {maturity['score_percent']}% ({maturity['label']})",
            f"- Measured decisions: {performance['measured_1d_decisions']}",
            f"- Graduation checks: {maturity['graduation_passed_checks']} / {maturity['graduation_total_checks']}",
            "",
            "## System Health",
            "",
            f"- Jobs recorded: {health['total_jobs']}",
            f"- Intelligence cycles: {health['intelligence_cycles']}",
            f"- Healthy completion: {health['healthy_completion_percent']}%",
            f"- Successful/warnings/failed/abandoned: {health['succeeded']} / {health['succeeded_with_warnings']} / {health['failed']} / {health['abandoned_running']}",
            f"- Average completed cycle duration: {health['average_cycle_duration_seconds']} seconds",
            "",
            "## Research Activity",
            "",
            f"- Research runs: {research['research_runs']}",
            f"- Items created/skipped/failed: {research['created_count']} / {research['skipped_count']} / {research['failure_count']}",
            f"- Skip rate: {research['skip_rate_percent']}%",
            f"- Articles fetched / signals stored: {research['articles_fetched']} / {research['signals_stored']}",
            "",
            "## Decision Intelligence",
            "",
            f"- Shadow decisions: {decisions['shadow_decisions']}",
            f"- Eligible decisions: {decisions['eligible_decisions']}",
            f"- Opportunities seen / skipped: {decisions['opportunities_seen']} / {decisions['decisions_skipped']}",
            f"- Average confidence: {decisions['average_confidence_percent']}%",
            "",
            "## Confidence Calibration",
            "",
            f"- Average snapshot confidence: {confidence['average_snapshot_confidence_percent']}%",
            f"- Latest snapshot confidence: {confidence['latest_snapshot_confidence_percent']}%",
            f"- Calibration sample: {confidence['calibration_sample_size']} decisions",
            "",
            "## Sector Leaders",
            "",
        ]
        for item in review["sector_analytics"][:5]:
            lines.append(
                f"- {item['sector']}: {item['decision_count']} decisions, "
                f"{item['directional_accuracy_percent']}% directional accuracy "
                f"across {item['measured_count']} measured outcomes"
            )
        lines.extend(["", "## Insights and Recommendations", ""])
        lines.extend(f"- {item}" for item in review["insights"])
        return "\n".join(lines) + "\n"

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
        return connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone() is not None

    def _rows_between(self, connection: sqlite3.Connection, *, table: str, timestamp_column: str, window: ReviewWindow) -> list[sqlite3.Row]:
        if not self._table_exists(connection, table):
            return []
        return list(connection.execute(
            f"SELECT * FROM {table} WHERE {timestamp_column} >= ? AND {timestamp_column} < ? ORDER BY {timestamp_column}",
            (window.start.isoformat(), window.end.isoformat()),
        ).fetchall())

    @staticmethod
    def _json(value: Any, default: Any) -> Any:
        if value is None:
            return default
        try:
            return json.loads(str(value))
        except (json.JSONDecodeError, TypeError, ValueError):
            return default

    @staticmethod
    def _day(value: Any) -> str | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value)).date().isoformat()
        except ValueError:
            return None

    def _job_summary(self, jobs: list[sqlite3.Row]) -> dict[str, Any]:
        statuses = Counter(str(row["status"]) for row in jobs)
        intelligence = [row for row in jobs if str(row["job_type"]) == "INTELLIGENCE_CYCLE"]
        durations: list[float] = []
        stage_warnings = Counter()
        for row in intelligence:
            if str(row["status"]) in {"SUCCEEDED", "SUCCEEDED_WITH_WARNINGS"} and row["started_at"] and row["finished_at"]:
                try:
                    duration = max(0.0, (datetime.fromisoformat(str(row["finished_at"])) - datetime.fromisoformat(str(row["started_at"]))).total_seconds())
                    if duration <= 3600:
                        durations.append(duration)
                except ValueError:
                    pass
            result = self._json(row["result_json"], {})
            for stage in result.get("stages", []):
                warnings = stage.get("warnings") or []
                if warnings:
                    stage_warnings[str(stage.get("stage", "UNKNOWN"))] += len(warnings)
        completed = statuses["SUCCEEDED"] + statuses["SUCCEEDED_WITH_WARNINGS"] + statuses["FAILED"]
        denominator = max(1, len(jobs))
        return {
            "total_jobs": len(jobs),
            "intelligence_cycles": len(intelligence),
            "succeeded": statuses["SUCCEEDED"],
            "succeeded_with_warnings": statuses["SUCCEEDED_WITH_WARNINGS"],
            "failed": statuses["FAILED"],
            "queued": statuses["QUEUED"],
            "abandoned_running": statuses["RUNNING"],
            "completion_rate_percent": round(completed / denominator * 100, 1),
            "healthy_completion_percent": round((statuses["SUCCEEDED"] + statuses["SUCCEEDED_WITH_WARNINGS"]) / denominator * 100, 1),
            "average_cycle_duration_seconds": round(mean(durations), 2) if durations else 0.0,
            "longest_cycle_duration_seconds": round(max(durations), 2) if durations else 0.0,
            "warning_stages": dict(stage_warnings.most_common()),
        }

    def _research_summary(self, runs: list[sqlite3.Row], jobs: list[sqlite3.Row]) -> dict[str, Any]:
        research_runs = [row for row in runs if "RESEARCH" in str(row["run_type"])]
        created = sum(int(row["created_count"] or 0) for row in research_runs)
        skipped = sum(int(row["skipped_count"] or 0) for row in research_runs)
        failures = sum(int(row["failure_count"] or 0) for row in research_runs)
        articles_fetched = 0
        signals_stored = 0
        provider_counts = Counter()
        for row in jobs:
            if str(row["job_type"]) != "INTELLIGENCE_CYCLE":
                continue
            result = self._json(row["result_json"], {})
            for stage in result.get("stages", []):
                if stage.get("stage") != "NEWS_RESEARCH":
                    continue
                detail = stage.get("detail", {})
                articles_fetched += int(detail.get("articles_fetched", 0) or 0)
                signals_stored += int(detail.get("signals_stored", 0) or 0)
                provider = detail.get("provider")
                if provider:
                    provider_counts[str(provider)] += 1
        total_items = created + skipped + failures
        return {
            "research_runs": len(research_runs),
            "created_count": created,
            "skipped_count": skipped,
            "failure_count": failures,
            "skip_rate_percent": round(skipped / max(1, total_items) * 100, 1),
            "articles_fetched": articles_fetched,
            "signals_stored": signals_stored,
            "provider_cycles": dict(provider_counts),
        }

    def _decision_summary(self, decisions: list[sqlite3.Row], memories: list[sqlite3.Row]) -> dict[str, Any]:
        action_counts = Counter(str(row["action"]) for row in decisions)
        symbol_counts = Counter(str(row["symbol"]) for row in decisions)
        confidence_values = [float(row["confidence"]) for row in decisions if row["confidence"] is not None]
        eligible = sum(1 for row in decisions if int(row["eligible_for_trade"] or 0) == 1)
        recommendation_counts = Counter(str(row["recommendation"]) for row in memories)
        return {
            "shadow_decisions": len(decisions),
            "eligible_decisions": eligible,
            "eligibility_rate_percent": round(eligible / max(1, len(decisions)) * 100, 1),
            "average_confidence_percent": round(mean(confidence_values) * 100, 1) if confidence_values else 0.0,
            "actions": dict(action_counts),
            "top_symbols": [{"symbol": symbol, "count": count} for symbol, count in symbol_counts.most_common(10)],
            "memory_decisions": len(memories),
            "recommendations": dict(recommendation_counts),
            "opportunities_seen": 0,
            "decisions_skipped": 0,
        }

    def _outcome_summary(self, outcomes: list[sqlite3.Row], jobs: list[sqlite3.Row]) -> dict[str, Any]:
        latest: dict[str, Any] = {"total_decisions": 0, "measured_1d_decisions": 0, "directional_success_percent": 0.0, "profitable_after_cost_percent": 0.0}
        outcomes_recorded_by_cycles = snapshots_captured = price_failures = opportunities = decisions_skipped = 0
        for row in jobs:
            if str(row["job_type"]) != "INTELLIGENCE_CYCLE":
                continue
            result = self._json(row["result_json"], {})
            for stage in result.get("stages", []):
                detail = stage.get("detail", {})
                if stage.get("stage") == "SHADOW_PERFORMANCE":
                    latest = {
                        "total_decisions": int(detail.get("total_decisions", 0) or 0),
                        "measured_1d_decisions": int(detail.get("measured_1d_decisions", 0) or 0),
                        "directional_success_percent": float(detail.get("directional_success_percent", 0.0) or 0.0),
                        "profitable_after_cost_percent": float(detail.get("profitable_after_cost_percent", 0.0) or 0.0),
                    }
                elif stage.get("stage") == "CAPTURE_PRICE_OUTCOMES":
                    outcomes_recorded_by_cycles += int(detail.get("outcomes_recorded", 0) or 0)
                    snapshots_captured += int(detail.get("snapshots_captured", 0) or 0)
                    price_failures += int(detail.get("failure_count", 0) or 0)
                elif stage.get("stage") == "SHADOW_ANALYSIS":
                    opportunities += int(detail.get("opportunities_seen", 0) or 0)
                    decisions_skipped += int(detail.get("decisions_skipped", 0) or 0)
        returns = [float(row["absolute_return"]) for row in outcomes if row["absolute_return"] is not None]
        latest.update({
            "recorded_outcomes": len(outcomes),
            "outcomes_recorded_by_cycles": outcomes_recorded_by_cycles,
            "snapshots_captured": snapshots_captured,
            "price_operation_failures": price_failures,
            "average_recorded_return_percent": round(mean(returns) * 100, 3) if returns else 0.0,
            "opportunities_seen": opportunities,
            "decisions_skipped": decisions_skipped,
        })
        return latest

    @staticmethod
    def _outcomes_by_decision(outcomes: list[sqlite3.Row]) -> dict[str, sqlite3.Row]:
        selected: dict[str, sqlite3.Row] = {}
        for row in outcomes:
            decision_id = str(row["decision_id"])
            current = selected.get(decision_id)
            if current is None:
                selected[decision_id] = row
                continue
            current_horizon = int(current["horizon_days"] or 999)
            horizon = int(row["horizon_days"] or 999)
            if horizon == 1 or horizon < current_horizon:
                selected[decision_id] = row
        return selected

    @staticmethod
    def _directional_success(decision: sqlite3.Row, outcome: sqlite3.Row) -> bool | None:
        value = outcome["absolute_return"]
        if value is None:
            return None
        sentiment = str(decision["sentiment"] or "").upper()
        result = float(value)
        if sentiment == "POSITIVE":
            return result > 0
        if sentiment == "NEGATIVE":
            return result < 0
        return None

    def _confidence_summary(self, snapshots: list[sqlite3.Row], decisions: list[sqlite3.Row], outcome_index: dict[str, sqlite3.Row]) -> dict[str, Any]:
        snapshot_confidence = [float(row["confidence"]) for row in snapshots if row["confidence"] is not None]
        latest_confidence = snapshot_confidence[-1] if snapshot_confidence else 0.0
        stale_count = sum(1 for row in snapshots if str(row["overall_status"]).upper() == "STALE")
        bucket_defs = [("Below 60%", 0, 60), ("60–69%", 60, 70), ("70–79%", 70, 80), ("80–89%", 80, 90), ("90%+", 90, 101)]
        buckets = []
        measured_total = 0
        for label, lower, upper in bucket_defs:
            bucket_decisions = [row for row in decisions if lower <= float(row["confidence"] or 0.0) * 100 < upper]
            measured = []
            returns = []
            for row in bucket_decisions:
                outcome = outcome_index.get(str(row["decision_id"]))
                if outcome is None:
                    continue
                success = self._directional_success(row, outcome)
                if success is not None:
                    measured.append(success)
                if outcome["absolute_return"] is not None:
                    returns.append(float(outcome["absolute_return"]) * 100)
            measured_total += len(measured)
            expected = round(mean([float(row["confidence"] or 0.0) * 100 for row in bucket_decisions]), 1) if bucket_decisions else 0.0
            actual = round(sum(measured) / len(measured) * 100, 1) if measured else 0.0
            buckets.append({
                "label": label,
                "decision_count": len(bucket_decisions),
                "measured_count": len(measured),
                "expected_accuracy_percent": expected,
                "actual_accuracy_percent": actual,
                "calibration_gap_points": round(actual - expected, 1) if measured else 0.0,
                "average_return_percent": round(mean(returns), 3) if returns else 0.0,
            })
        actual_values = [item["actual_accuracy_percent"] for item in buckets if item["measured_count"]]
        expected_values = [item["expected_accuracy_percent"] for item in buckets if item["measured_count"]]
        mean_gap = round(mean([abs(a - e) for a, e in zip(actual_values, expected_values)]), 1) if actual_values else 0.0
        return {
            "snapshot_count": len(snapshots),
            "average_snapshot_confidence_percent": round(mean(snapshot_confidence) * 100, 1) if snapshot_confidence else 0.0,
            "latest_snapshot_confidence_percent": round(latest_confidence * 100, 1),
            "stale_snapshot_percent": round(stale_count / max(1, len(snapshots)) * 100, 1),
            "decision_confidence_bands": {item["label"]: item["decision_count"] for item in buckets},
            "calibration_buckets": buckets,
            "calibration_sample_size": measured_total,
            "mean_absolute_calibration_gap_points": mean_gap,
        }

    def _sector_analytics(self, decisions: list[sqlite3.Row], outcome_index: dict[str, sqlite3.Row]) -> list[dict[str, Any]]:
        grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in decisions:
            grouped[SYMBOL_TO_SECTOR.get(str(row["symbol"]).upper(), "Other")].append(row)
        output = []
        for sector, items in grouped.items():
            measured: list[bool] = []
            returns: list[float] = []
            confidence = [float(row["confidence"] or 0.0) * 100 for row in items]
            for row in items:
                outcome = outcome_index.get(str(row["decision_id"]))
                if outcome is None:
                    continue
                success = self._directional_success(row, outcome)
                if success is not None:
                    measured.append(success)
                if outcome["absolute_return"] is not None:
                    returns.append(float(outcome["absolute_return"]) * 100)
            output.append({
                "sector": sector,
                "decision_count": len(items),
                "measured_count": len(measured),
                "average_confidence_percent": round(mean(confidence), 1) if confidence else 0.0,
                "directional_accuracy_percent": round(sum(measured) / len(measured) * 100, 1) if measured else 0.0,
                "average_return_percent": round(mean(returns), 3) if returns else 0.0,
                "eligible_count": sum(1 for row in items if int(row["eligible_for_trade"] or 0) == 1),
            })
        return sorted(output, key=lambda item: (item["measured_count"], item["decision_count"], item["average_confidence_percent"]), reverse=True)

    def _symbol_analytics(self, decisions: list[sqlite3.Row], outcome_index: dict[str, sqlite3.Row]) -> list[dict[str, Any]]:
        grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in decisions:
            grouped[str(row["symbol"]).upper()].append(row)
        output = []
        for symbol, items in grouped.items():
            measured: list[bool] = []
            returns: list[float] = []
            for row in items:
                outcome = outcome_index.get(str(row["decision_id"]))
                if outcome is None:
                    continue
                success = self._directional_success(row, outcome)
                if success is not None:
                    measured.append(success)
                if outcome["absolute_return"] is not None:
                    returns.append(float(outcome["absolute_return"]) * 100)
            output.append({
                "symbol": symbol,
                "sector": SYMBOL_TO_SECTOR.get(symbol, "Other"),
                "decision_count": len(items),
                "measured_count": len(measured),
                "average_confidence_percent": round(mean([float(row["confidence"] or 0.0) * 100 for row in items]), 1),
                "average_score": round(mean([float(row["score"] or 0.0) for row in items]), 2),
                "directional_accuracy_percent": round(sum(measured) / len(measured) * 100, 1) if measured else 0.0,
                "average_return_percent": round(mean(returns), 3) if returns else 0.0,
                "eligible_count": sum(1 for row in items if int(row["eligible_for_trade"] or 0) == 1),
                "latest_headline": str(items[-1]["headline"] or ""),
            })
        return sorted(output, key=lambda item: (item["measured_count"], item["decision_count"], item["average_score"]), reverse=True)[:50]

    def _blocker_analytics(self, decisions: list[sqlite3.Row], memories: list[sqlite3.Row]) -> dict[str, Any]:
        counts = Counter()
        affected = Counter()
        for row in decisions:
            symbol = str(row["symbol"])
            for blocker in self._json(row["blocking_reasons_json"], []):
                cleaned = str(blocker).strip()
                if cleaned:
                    counts[cleaned] += 1
                    affected[(cleaned, symbol)] += 1
        for row in memories:
            symbol = str(row["symbol"])
            for blocker in self._json(row["blockers_json"], []):
                cleaned = str(blocker).strip()
                if cleaned:
                    counts[cleaned] += 1
                    affected[(cleaned, symbol)] += 1
        top = []
        for blocker, count in counts.most_common(12):
            symbols = sorted({symbol for (reason, symbol), _ in affected.items() if reason == blocker})
            top.append({"reason": blocker, "count": count, "symbol_count": len(symbols), "symbols": symbols[:8]})
        return {"total_blocker_events": sum(counts.values()), "unique_blockers": len(counts), "top_blockers": top}

    def _trends(self, window: ReviewWindow, jobs: list[sqlite3.Row], runs: list[sqlite3.Row], decisions: list[sqlite3.Row], outcomes: list[sqlite3.Row]) -> list[dict[str, Any]]:
        days: dict[str, dict[str, Any]] = {}
        cursor = window.start.date()
        while cursor <= window.end.date():
            key = cursor.isoformat()
            days[key] = {"date": key, "cycles": 0, "healthy_cycles": 0, "failed_cycles": 0, "created": 0, "skipped": 0, "decisions": 0, "measured_outcomes": 0, "cycle_duration_seconds": 0.0}
            cursor += timedelta(days=1)
        durations: dict[str, list[float]] = defaultdict(list)
        for row in jobs:
            day = self._day(row["created_at"])
            if day not in days or str(row["job_type"]) != "INTELLIGENCE_CYCLE":
                continue
            days[day]["cycles"] += 1
            if str(row["status"]) in {"SUCCEEDED", "SUCCEEDED_WITH_WARNINGS"}:
                days[day]["healthy_cycles"] += 1
            if str(row["status"]) == "FAILED":
                days[day]["failed_cycles"] += 1
            if row["started_at"] and row["finished_at"]:
                try:
                    value = max(0.0, (datetime.fromisoformat(str(row["finished_at"])) - datetime.fromisoformat(str(row["started_at"]))).total_seconds())
                    if value <= 3600:
                        durations[day].append(value)
                except ValueError:
                    pass
        for row in runs:
            day = self._day(row["started_at"])
            if day in days and "RESEARCH" in str(row["run_type"]):
                days[day]["created"] += int(row["created_count"] or 0)
                days[day]["skipped"] += int(row["skipped_count"] or 0)
        for row in decisions:
            day = self._day(row["created_at"])
            if day in days:
                days[day]["decisions"] += 1
        for row in outcomes:
            day = self._day(row["observed_at"])
            if day in days:
                days[day]["measured_outcomes"] += 1
        for day, values in durations.items():
            days[day]["cycle_duration_seconds"] = round(mean(values), 2) if values else 0.0
        return list(days.values())

    def _maturity(self, snapshots: list[sqlite3.Row], decision_summary: dict[str, Any], outcome_summary: dict[str, Any], job_summary: dict[str, Any]) -> dict[str, Any]:
        latest = snapshots[-1] if snapshots else None
        passed = int(latest["graduation_passed_checks"] or 0) if latest else 0
        total = int(latest["graduation_total_checks"] or 0) if latest else 0
        reliability_component = min(25.0, job_summary["healthy_completion_percent"] / 100 * 25)
        sample_component = min(30.0, outcome_summary["measured_1d_decisions"] / 150 * 30)
        decision_component = min(20.0, decision_summary["shadow_decisions"] / 250 * 20)
        graduation_component = (passed / max(1, total)) * 25
        score = round(reliability_component + sample_component + decision_component + graduation_component, 1)
        if score < 25:
            label = "Foundation"
        elif score < 50:
            label = "Learning"
        elif score < 75:
            label = "Validation"
        elif score < 90:
            label = "Live candidate"
        else:
            label = "Mature"
        return {
            "score_percent": score,
            "label": label,
            "graduation_passed_checks": passed,
            "graduation_total_checks": total,
            "trading_readiness": str(latest["trading_readiness"] or "UNKNOWN") if latest else "UNKNOWN",
            "evidence_quality": str(latest["evidence_quality"] or "UNKNOWN") if latest else "UNKNOWN",
            "components": {
                "reliability": round(reliability_component, 1),
                "measured_sample": round(sample_component, 1),
                "decision_history": round(decision_component, 1),
                "graduation": round(graduation_component, 1),
            },
        }

    @staticmethod
    def _executive_summary(*, job_summary: dict[str, Any], research_summary: dict[str, Any], decision_summary: dict[str, Any], outcome_summary: dict[str, Any], sector_analytics: list[dict[str, Any]]) -> str:
        leader = next((item for item in sector_analytics if item["measured_count"]), None)
        sector_text = ""
        if leader:
            sector_text = f" {leader['sector']} currently has the strongest measured sector record at {leader['directional_accuracy_percent']}% across {leader['measured_count']} outcomes."
        return (
            f"KAIRO recorded {job_summary['intelligence_cycles']} intelligence cycles with "
            f"{job_summary['healthy_completion_percent']}% completing successfully or with warnings. "
            f"Research created {research_summary['created_count']} items and skipped {research_summary['skipped_count']}. "
            f"The platform generated {decision_summary['shadow_decisions']} shadow decisions; "
            f"{outcome_summary['measured_1d_decisions']} have a measured one-day outcome, with "
            f"{outcome_summary['directional_success_percent']}% directional success.{sector_text}"
        )

    @staticmethod
    def _insights(*, job_summary: dict[str, Any], research_summary: dict[str, Any], decision_summary: dict[str, Any], outcome_summary: dict[str, Any], confidence_summary: dict[str, Any], sector_analytics: list[dict[str, Any]], blocker_analytics: dict[str, Any]) -> list[str]:
        insights: list[str] = []
        if job_summary["abandoned_running"]:
            insights.append(f"{job_summary['abandoned_running']} jobs remain RUNNING in the selected period; investigate worker interruptions before judging strategy quality.")
        elif job_summary["healthy_completion_percent"] >= 95:
            insights.append("Operational completion was strong in the selected period.")
        else:
            insights.append("Operational completion is below the 95% reliability target; continue reliability monitoring.")
        if research_summary["skip_rate_percent"] >= 90:
            insights.append("Research skip rate is very high. Compare 30-minute and hourly cycles to confirm the extra cadence adds new signals rather than duplicate work.")
        if outcome_summary["measured_1d_decisions"] < 100:
            insights.append("The measured decision sample is still too small for strategy conclusions; 100–200 matured decisions is the first serious review point.")
        if confidence_summary["calibration_sample_size"] and confidence_summary["mean_absolute_calibration_gap_points"] >= 15:
            insights.append(f"Confidence calibration is currently separated from measured accuracy by {confidence_summary['mean_absolute_calibration_gap_points']} percentage points on average.")
        elif confidence_summary["calibration_sample_size"] == 0:
            insights.append("No decision-level outcomes are available for confidence calibration yet; the calibration chart will become meaningful as outcomes mature.")
        if outcome_summary["price_operation_failures"]:
            insights.append(f"Price outcome capture recorded {outcome_summary['price_operation_failures']} failed or deferred operations; central market-data rate limiting and caching remains a priority.")
        measured_sectors = [item for item in sector_analytics if item["measured_count"] >= 3]
        if measured_sectors:
            best = max(measured_sectors, key=lambda item: item["directional_accuracy_percent"])
            insights.append(f"{best['sector']} is the strongest measured sector in this period at {best['directional_accuracy_percent']}% directional accuracy across {best['measured_count']} outcomes.")
        if blocker_analytics["top_blockers"]:
            top = blocker_analytics["top_blockers"][0]
            insights.append(f"The most frequent decision blocker was “{top['reason']}” ({top['count']} occurrences).")
        if decision_summary["shadow_decisions"] == 0:
            insights.append("No new shadow decisions were created in the selected period; verify this reflects selectivity rather than stale inputs.")
        return insights
