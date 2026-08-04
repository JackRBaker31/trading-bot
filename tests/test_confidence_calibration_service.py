from types import SimpleNamespace

from app.confidence_calibration_service import ConfidenceCalibrationService


class ReviewStub:
    def __init__(self):
        self.calls = 0

    def generate(self, **kwargs):
        self.calls += 1
        error = 18.0 if self.calls == 1 else 10.0
        return {
            "confidence_calibration": {
                "calibration_sample_size": 83,
                "mean_absolute_calibration_gap_points": error,
                "calibration_buckets": [
                    {
                        "name": "HIGH",
                        "label": "High",
                        "measured_count": 40,
                        "expected_accuracy_percent": 85.0,
                        "actual_accuracy_percent": 50.0,
                        "calibration_gap_points": -35.0,
                    }
                ],
            }
        }


def test_generates_read_only_calibration_report():
    report = ConfidenceCalibrationService(review_service=ReviewStub()).generate(days=7)
    assert report["trading_impact"] == "NONE"
    assert report["automatic_model_changes"] is False
    assert report["summary"]["sample_size"] == 83
    assert report["summary"]["drift_status"] == "WORSENING"
    assert report["buckets"][0]["assessment"] == "POORLY_CALIBRATED"
    assert report["recommendations"]
