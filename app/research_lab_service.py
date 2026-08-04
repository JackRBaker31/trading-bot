from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.performance_review_service import PerformanceReviewService


class ResearchLabService:
    """Deterministic, evidence-backed research brief over existing KAIRO history.

    Package 1.1 is read-only. It proposes research experiments but never changes
    model weights, graduation rules, risk controls, or execution behaviour.
    """

    def __init__(self, *, review_service: PerformanceReviewService) -> None:
        self._review_service = review_service

    def generate(self, *, days: int = 7) -> dict[str, Any]:
        if days not in {1, 7, 30}:
            raise ValueError("Research Lab days must be 1, 7, or 30.")
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        review = self._review_service.generate(start=start, end=end)
        findings = self._findings(review)
        experiments = self._experiments(review)
        return {
            "generated_at": end.isoformat(),
            "period": review["period"],
            "status": "EVIDENCE_BUILDING" if review["shadow_performance"]["measured_1d_decisions"] < 150 else "REVIEW_READY",
            "trading_impact": "NONE",
            "headline": self._headline(review),
            "summary": review["executive_summary"],
            "evidence": {
                "shadow_decisions": review["decision_intelligence"]["shadow_decisions"],
                "measured_1d_decisions": review["shadow_performance"]["measured_1d_decisions"],
                "directional_success_percent": review["shadow_performance"]["directional_success_percent"],
                "profitable_after_cost_percent": review["shadow_performance"]["profitable_after_cost_percent"],
                "calibration_sample_size": review["confidence_calibration"]["calibration_sample_size"],
                "healthy_completion_percent": review["system_health"]["healthy_completion_percent"],
            },
            "findings": findings,
            "suggested_experiments": experiments,
            "sector_leaders": review["sector_analytics"][:5],
            "confidence_buckets": review["confidence_calibration"]["calibration_buckets"],
            "timeline": [
                {
                    "date": row["date"],
                    "decisions": row["decisions"],
                    "measured_outcomes": row["measured_outcomes"],
                    "healthy_cycles": row["healthy_cycles"],
                    "failed_cycles": row["failed_cycles"],
                }
                for row in review["trends"][-14:]
            ],
            "methodology": {
                "deterministic": True,
                "external_language_model": False,
                "automatic_model_changes": False,
                "minimum_serious_review_sample": 150,
                "source": "KAIRO SQLite decision, outcome, ranking and job history",
            },
        }

    @staticmethod
    def _headline(review: dict[str, Any]) -> str:
        measured = review["shadow_performance"]["measured_1d_decisions"]
        if measured < 50:
            return "Research evidence is still forming"
        if review["shadow_performance"]["profitable_after_cost_percent"] >= 53:
            return "Measured evidence is approaching the current profitability gate"
        return "Evidence is maturing, but the current shadow model remains below graduation targets"

    def _findings(self, review: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        perf = review["shadow_performance"]
        confidence = review["confidence_calibration"]
        sectors = [item for item in review["sector_analytics"] if item["measured_count"] > 0]

        findings.append({
            "kind": "PERFORMANCE",
            "title": "One-day shadow evidence",
            "statement": f"{perf['measured_1d_decisions']} one-day decisions are measured; {perf['directional_success_percent']}% were directionally successful and {perf['profitable_after_cost_percent']}% were profitable after costs.",
            "sample_size": perf["measured_1d_decisions"],
            "confidence": "LIMITED" if perf["measured_1d_decisions"] < 150 else "MODERATE",
        })
        if sectors:
            best = max(sectors, key=lambda x: (x["directional_accuracy_percent"], x["measured_count"]))
            worst = min(sectors, key=lambda x: (x["directional_accuracy_percent"], -x["measured_count"]))
            findings.extend([
                {
                    "kind": "SECTOR",
                    "title": "Strongest measured sector",
                    "statement": f"{best['sector']} currently leads with {best['directional_accuracy_percent']}% directional accuracy across {best['measured_count']} measured decisions.",
                    "sample_size": best["measured_count"],
                    "confidence": "LIMITED" if best["measured_count"] < 30 else "MODERATE",
                },
                {
                    "kind": "SECTOR",
                    "title": "Weakest measured sector",
                    "statement": f"{worst['sector']} currently trails with {worst['directional_accuracy_percent']}% directional accuracy across {worst['measured_count']} measured decisions.",
                    "sample_size": worst["measured_count"],
                    "confidence": "LIMITED" if worst["measured_count"] < 30 else "MODERATE",
                },
            ])
        buckets = [b for b in confidence["calibration_buckets"] if b["measured_count"] > 0]
        if buckets:
            largest_gap = max(buckets, key=lambda b: abs(b["calibration_gap_points"]))
            findings.append({
                "kind": "CALIBRATION",
                "title": "Largest confidence gap",
                "statement": f"The {largest_gap['label']} band has a {largest_gap['calibration_gap_points']} point expected-versus-measured accuracy gap across {largest_gap['measured_count']} outcomes.",
                "sample_size": largest_gap["measured_count"],
                "confidence": "LIMITED" if largest_gap["measured_count"] < 30 else "MODERATE",
            })
        return findings

    def _experiments(self, review: dict[str, Any]) -> list[dict[str, Any]]:
        experiments: list[dict[str, Any]] = []
        perf = review["shadow_performance"]
        confidence = review["confidence_calibration"]
        if perf["measured_1d_decisions"] < 150:
            experiments.append({
                "experiment_id": "EVIDENCE-001",
                "title": "Continue unchanged evidence collection",
                "hypothesis": "Holding the current model and universe constant will produce a cleaner graduation-quality baseline.",
                "status": "RECOMMENDED",
                "risk": "LOW",
                "required_sample": 150,
                "current_sample": perf["measured_1d_decisions"],
                "automatic_change": False,
            })
        if confidence["calibration_sample_size"] >= 30 and confidence["mean_absolute_calibration_gap_points"] >= 10:
            experiments.append({
                "experiment_id": "CALIBRATION-001",
                "title": "Shadow confidence recalibration",
                "hypothesis": "A calibrated confidence mapping may better align displayed confidence with realised directional accuracy.",
                "status": "PROPOSED",
                "risk": "LOW",
                "required_sample": max(100, confidence["calibration_sample_size"]),
                "current_sample": confidence["calibration_sample_size"],
                "automatic_change": False,
            })
        weak = [s for s in review["sector_analytics"] if s["measured_count"] >= 20 and s["directional_accuracy_percent"] < 45]
        if weak:
            sector = sorted(weak, key=lambda x: x["directional_accuracy_percent"])[0]
            experiments.append({
                "experiment_id": "SECTOR-001",
                "title": f"Review {sector['sector']} evidence weighting",
                "hypothesis": f"A shadow-only sector-specific penalty may reduce weak {sector['sector']} candidates without changing the production model.",
                "status": "PROPOSED",
                "risk": "MEDIUM",
                "required_sample": 100,
                "current_sample": sector["measured_count"],
                "automatic_change": False,
            })
        return experiments
