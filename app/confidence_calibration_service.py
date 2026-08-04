from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.performance_review_service import PerformanceReviewService


class ConfidenceCalibrationService:
    """Read-only calibration analytics over existing shadow-decision outcomes."""

    VALID_DAYS = {1, 7, 30}

    def __init__(self, *, review_service: PerformanceReviewService) -> None:
        self._review_service = review_service

    def generate(self, *, days: int = 7) -> dict[str, Any]:
        if days not in self.VALID_DAYS:
            raise ValueError("Confidence calibration days must be 1, 7, or 30.")

        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)
        current = self._review_service.generate(start=current_start, end=now)
        previous = self._review_service.generate(start=previous_start, end=current_start)

        current_cal = current["confidence_calibration"]
        previous_cal = previous["confidence_calibration"]
        buckets = [self._normalise_bucket(item) for item in current_cal["calibration_buckets"]]
        measured = int(current_cal["calibration_sample_size"])
        mae = float(current_cal["mean_absolute_calibration_gap_points"])
        previous_mae = float(previous_cal["mean_absolute_calibration_gap_points"])
        drift_points = round(mae - previous_mae, 1)

        return {
            "generated_at": now.isoformat(),
            "period_days": days,
            "status": self._status(measured=measured, mae=mae),
            "trading_impact": "NONE",
            "automatic_model_changes": False,
            "summary": {
                "sample_size": measured,
                "mean_absolute_error_points": round(mae, 1),
                "previous_error_points": round(previous_mae, 1),
                "drift_points": drift_points,
                "drift_status": self._drift_status(drift_points, measured),
                "best_band": self._best_band(buckets),
                "weakest_band": self._weakest_band(buckets),
            },
            "buckets": buckets,
            "recommendations": self._recommendations(measured, mae, drift_points, buckets),
            "methodology": {
                "outcome_horizon": "1D",
                "expected_measure": "average stored confidence",
                "observed_measure": "directional success percentage",
                "minimum_review_sample": 150,
                "minimum_band_sample": 30,
                "deterministic": True,
                "external_language_model": False,
            },
        }

    @staticmethod
    def _normalise_bucket(item: dict[str, Any]) -> dict[str, Any]:
        expected = float(item.get("expected_accuracy_percent", 0.0))
        observed = float(item.get("actual_accuracy_percent", 0.0))
        gap = float(item.get("calibration_gap_points", observed - expected))
        sample = int(item.get("measured_count", 0))
        return {
            "name": str(item.get("name", item.get("label", "UNKNOWN"))),
            "label": str(item.get("label", item.get("name", "Unknown"))),
            "measured_count": sample,
            "expected_accuracy_percent": round(expected, 1),
            "observed_accuracy_percent": round(observed, 1),
            "calibration_gap_points": round(gap, 1),
            "absolute_gap_points": round(abs(gap), 1),
            "assessment": ConfidenceCalibrationService._band_assessment(sample, abs(gap)),
        }

    @staticmethod
    def _band_assessment(sample: int, gap: float) -> str:
        if sample < 30:
            return "INSUFFICIENT_SAMPLE"
        if gap <= 5:
            return "WELL_CALIBRATED"
        if gap <= 10:
            return "ACCEPTABLE"
        if gap <= 20:
            return "MISALIGNED"
        return "POORLY_CALIBRATED"

    @staticmethod
    def _status(*, measured: int, mae: float) -> str:
        if measured < 30:
            return "EVIDENCE_BUILDING"
        if measured < 150:
            return "PRELIMINARY"
        if mae <= 10:
            return "CALIBRATED"
        return "RECALIBRATION_REVIEW"

    @staticmethod
    def _drift_status(drift: float, measured: int) -> str:
        if measured < 30:
            return "INSUFFICIENT_EVIDENCE"
        if drift >= 5:
            return "WORSENING"
        if drift <= -5:
            return "IMPROVING"
        return "STABLE"

    @staticmethod
    def _best_band(buckets: list[dict[str, Any]]) -> str | None:
        eligible = [b for b in buckets if b["measured_count"] > 0]
        return min(eligible, key=lambda b: b["absolute_gap_points"])["label"] if eligible else None

    @staticmethod
    def _weakest_band(buckets: list[dict[str, Any]]) -> str | None:
        eligible = [b for b in buckets if b["measured_count"] > 0]
        return max(eligible, key=lambda b: b["absolute_gap_points"])["label"] if eligible else None

    @staticmethod
    def _recommendations(measured: int, mae: float, drift: float, buckets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        if measured < 150:
            output.append({"code": "COLLECT_EVIDENCE", "title": "Continue unchanged evidence collection", "reason": f"{measured} measured 1D outcomes are available; 150 are required for the first serious calibration review.", "automatic_change": False})
        if mae >= 10 and measured >= 30:
            output.append({"code": "TEST_MAPPING", "title": "Propose a shadow-only confidence mapping experiment", "reason": f"Mean absolute calibration error is {mae:.1f} points.", "automatic_change": False})
        if drift >= 5 and measured >= 30:
            output.append({"code": "REVIEW_DRIFT", "title": "Review recent confidence drift", "reason": f"Calibration error worsened by {drift:.1f} points versus the previous equal period.", "automatic_change": False})
        weak = [b for b in buckets if b["measured_count"] >= 30 and b["absolute_gap_points"] >= 10]
        for bucket in weak[:2]:
            output.append({"code": "REVIEW_BAND", "title": f"Review {bucket['label']} confidence band", "reason": f"Observed accuracy differs from expected accuracy by {bucket['absolute_gap_points']:.1f} points across {bucket['measured_count']} outcomes.", "automatic_change": False})
        return output
