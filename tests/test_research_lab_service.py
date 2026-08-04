from datetime import datetime, timezone

from app.research_lab_service import ResearchLabService


class FakeReviewService:
    def generate(self, *, start, end):
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat(), "hours": 168},
            "executive_summary": "Evidence summary.",
            "system_health": {"healthy_completion_percent": 99.0},
            "decision_intelligence": {"shadow_decisions": 88},
            "shadow_performance": {"measured_1d_decisions": 83, "directional_success_percent": 36.14, "profitable_after_cost_percent": 33.73},
            "confidence_calibration": {"calibration_sample_size": 83, "mean_absolute_calibration_gap_points": 15.0, "calibration_buckets": [{"label":"HIGH","decision_count":83,"measured_count":83,"expected_accuracy_percent":80,"actual_accuracy_percent":36.14,"calibration_gap_points":-43.86,"average_return_percent":0.1}]},
            "sector_analytics": [{"sector":"Technology","decision_count":40,"measured_count":35,"average_confidence_percent":82,"directional_accuracy_percent":51,"average_return_percent":0.2,"eligible_count":0}],
            "trends": [{"date":"2026-08-04","decisions":3,"measured_outcomes":2,"healthy_cycles":10,"failed_cycles":0}],
        }


def test_research_lab_is_deterministic_and_read_only():
    result = ResearchLabService(review_service=FakeReviewService()).generate(days=7)
    assert result["trading_impact"] == "NONE"
    assert result["methodology"]["external_language_model"] is False
    assert result["methodology"]["automatic_model_changes"] is False
    assert result["evidence"]["measured_1d_decisions"] == 83
    assert result["findings"]
    assert result["suggested_experiments"]
