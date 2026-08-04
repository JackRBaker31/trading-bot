import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "@/test/handlers";
import ConfidenceCalibrationPage from "@/pages/ConfidenceCalibrationPage";

test("renders evidence-backed confidence calibration without changing the model", async () => {
  server.use(http.get("http://127.0.0.1:8000/api/confidence-calibration/report", () => HttpResponse.json({
    generated_at: "2026-08-04T10:00:00+00:00", period_days: 7, status: "PRELIMINARY", trading_impact: "NONE", automatic_model_changes: false,
    summary: { sample_size: 83, mean_absolute_error_points: 18.0, previous_error_points: 10.0, drift_points: 8.0, drift_status: "WORSENING", best_band: "High", weakest_band: "Very High" },
    buckets: [{ name: "HIGH", label: "High", measured_count: 40, expected_accuracy_percent: 85, observed_accuracy_percent: 50, calibration_gap_points: -35, absolute_gap_points: 35, assessment: "POORLY_CALIBRATED" }],
    recommendations: [{ code: "TEST_MAPPING", title: "Propose a shadow-only confidence mapping experiment", reason: "Calibration error is high.", automatic_change: false }],
    methodology: { outcome_horizon: "1D", expected_measure: "confidence", observed_measure: "success", minimum_review_sample: 150, minimum_band_sample: 30, deterministic: true, external_language_model: false }
  })));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><ConfidenceCalibrationPage /></QueryClientProvider>);
  expect(await screen.findByText("83")).toBeInTheDocument();
  expect(screen.getByText("18.0 pts")).toBeInTheDocument();
  expect(screen.getByText("POORLY CALIBRATED")).toBeInTheDocument();
  expect(screen.getByText("Automatic change: No")).toBeInTheDocument();
});
