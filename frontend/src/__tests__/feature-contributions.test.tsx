import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "@/test/handlers";
import FeatureContributionsPage from "@/pages/FeatureContributionsPage";

const BASE = "http://127.0.0.1:8000";

test("renders feature contribution evidence and safety boundary", async () => {
  server.use(http.get(`${BASE}/api/feature-contributions/report`, () => HttpResponse.json({
    generated_at: "2026-08-04T12:00:00Z", period: { days: 90, start: "2026-05-01T00:00:00Z", end: "2026-08-04T00:00:00Z" }, horizon_days: 1,
    status: "EVIDENCE_BUILDING", trading_impact: "NONE", automatic_weight_changes: false,
    summary: { tracked_snapshot_count: 88, measured_outcome_count: 83, feature_count: 2, positive_feature_count: 1, strongest_feature: "News", weakest_feature: "Risk" },
    features: [{ code: "NEWS", label: "News", snapshot_count: 88, measured_count: 83, average_contribution: 12.5, median_contribution: 12, directional_success_percent: 55, average_return_percent: 0.4, average_alpha_percent: 0.2, average_drawdown_percent: 1.1, contribution_return_correlation: 0.31, evidence: "MODERATE" }],
    latest_vectors: [{ snapshot_id: 1, captured_at: "2026-08-04T12:00:00Z", symbol: "AAPL", rank: 1, opportunity_score: 84, components: [{ code: "NEWS", label: "News", value: 12.5 }] }],
    recommendations: [{ code: "FEATURE-EVIDENCE-001", title: "Continue unchanged contribution collection", reason: "More evidence is required.", automatic_change: false, risk: "LOW" }], methodology: {},
  })));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><FeatureContributionsPage /></QueryClientProvider>);
  expect(await screen.findByText("Feature Contribution Engine")).toBeInTheDocument();
  expect(await screen.findByText("News")).toBeInTheDocument();
  expect(screen.getByText("Automatic change: No")).toBeInTheDocument();
  expect(screen.getByText(/Read-only analytics/)).toBeInTheDocument();
});
