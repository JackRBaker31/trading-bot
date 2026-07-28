import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import RankingValidationPage from "@/pages/RankingValidationPage";
import { render } from "@/test/test-utils";

const report = {
  generated_at: "2026-08-10T08:30:00Z",
  methodology_version: "KAIRO-RVALID-1.0",
  methodology_summary: "Forward return validation.",
  advisory_only: true,
  benchmark_symbol: "SPY",
  selected_horizon_days: 1,
  available_horizons: [1, 5, 20],
  tracked_snapshot_count: 18,
  measured_outcome_count: 12,
  pending_outcome_count: 42,
  latest_observed_at: "2026-08-10T08:00:00Z",
  selected_horizon: {
    horizon_days: 1,
    label: "1D",
    sample_count: 8,
    pending_count: 10,
    positive_count: 5,
    hit_rate_percent: 62.5,
    average_return_percent: 1.4,
    median_return_percent: 1.1,
    average_alpha_percent: 0.7,
    median_alpha_percent: 0.4,
    average_drawdown_percent: -1.2,
    top_three_average_return_percent: 2.1,
    other_average_return_percent: 0.3,
    score_return_correlation: 0.42,
    rank_return_correlation: 0.38,
    maturity: "IMMATURE",
  },
  horizons: [
    {
      horizon_days: 1,
      label: "1D",
      sample_count: 8,
      pending_count: 10,
      positive_count: 5,
      hit_rate_percent: 62.5,
      average_return_percent: 1.4,
      median_return_percent: 1.1,
      average_alpha_percent: 0.7,
      median_alpha_percent: 0.4,
      average_drawdown_percent: -1.2,
      top_three_average_return_percent: 2.1,
      other_average_return_percent: 0.3,
      score_return_correlation: 0.42,
      rank_return_correlation: 0.38,
      maturity: "IMMATURE",
    },
    {
      horizon_days: 5,
      label: "5D",
      sample_count: 3,
      pending_count: 15,
      positive_count: 2,
      hit_rate_percent: 66.7,
      average_return_percent: 2.8,
      median_return_percent: 2.5,
      average_alpha_percent: 1.2,
      median_alpha_percent: 1.0,
      average_drawdown_percent: -2.1,
      top_three_average_return_percent: 3.2,
      other_average_return_percent: 1.4,
      score_return_correlation: 0.5,
      rank_return_correlation: 0.4,
      maturity: "IMMATURE",
    },
    {
      horizon_days: 20,
      label: "20D",
      sample_count: 1,
      pending_count: 17,
      positive_count: 1,
      hit_rate_percent: 100,
      average_return_percent: 5.6,
      median_return_percent: 5.6,
      average_alpha_percent: 2.1,
      median_alpha_percent: 2.1,
      average_drawdown_percent: -3.2,
      top_three_average_return_percent: 5.6,
      other_average_return_percent: null,
      score_return_correlation: null,
      rank_return_correlation: null,
      maturity: "IMMATURE",
    },
  ],
  score_bands: [
    {
      code: "SCORE_80_PLUS",
      label: "Score 80–100",
      sample_count: 4,
      positive_count: 3,
      hit_rate_percent: 75,
      average_return_percent: 2.2,
      median_return_percent: 2.0,
      average_alpha_percent: 1.1,
      median_alpha_percent: 0.9,
      average_drawdown_percent: -1.0,
    },
  ],
  rank_buckets: [
    {
      code: "RANK_TOP_3",
      label: "Rank #1–#3",
      sample_count: 5,
      positive_count: 4,
      hit_rate_percent: 80,
      average_return_percent: 2.1,
      median_return_percent: 1.8,
      average_alpha_percent: 1.0,
      median_alpha_percent: 0.8,
      average_drawdown_percent: -1.1,
    },
    {
      code: "RANK_4_10",
      label: "Rank #4–#10",
      sample_count: 3,
      positive_count: 1,
      hit_rate_percent: 33.3,
      average_return_percent: 0.3,
      median_return_percent: 0.1,
      average_alpha_percent: -0.2,
      median_alpha_percent: -0.1,
      average_drawdown_percent: -1.5,
    },
  ],
  readiness_buckets: [
    {
      code: "EXECUTION_READY",
      label: "Execution ready",
      sample_count: 3,
      positive_count: 2,
      hit_rate_percent: 66.7,
      average_return_percent: 1.8,
      median_return_percent: 1.5,
      average_alpha_percent: 0.8,
      median_alpha_percent: 0.7,
      average_drawdown_percent: -1.0,
    },
    {
      code: "EXECUTION_BLOCKED",
      label: "Execution blocked",
      sample_count: 5,
      positive_count: 3,
      hit_rate_percent: 60,
      average_return_percent: 1.1,
      median_return_percent: 0.9,
      average_alpha_percent: 0.5,
      median_alpha_percent: 0.3,
      average_drawdown_percent: -1.3,
    },
  ],
  symbol_performance: [
    {
      code: "SYMBOL_AAPL",
      label: "AAPL",
      sample_count: 4,
      positive_count: 3,
      hit_rate_percent: 75,
      average_return_percent: 2.2,
      median_return_percent: 2.0,
      average_alpha_percent: 1.0,
      median_alpha_percent: 0.8,
      average_drawdown_percent: -1.0,
    },
  ],
  sector_performance: [
    {
      code: "SECTOR_TECHNOLOGY",
      label: "Technology",
      sample_count: 6,
      positive_count: 4,
      hit_rate_percent: 66.7,
      average_return_percent: 1.7,
      median_return_percent: 1.4,
      average_alpha_percent: 0.8,
      median_alpha_percent: 0.6,
      average_drawdown_percent: -1.2,
    },
  ],
  latest_outcomes: [
    {
      outcome_id: 1,
      snapshot_id: 20,
      captured_at: "2026-08-07T08:00:00Z",
      symbol: "AAPL",
      horizon_days: 1,
      entry_date: "2026-08-08",
      exit_date: "2026-08-08",
      observed_at: "2026-08-10T08:00:00Z",
      entry_price: 200,
      observed_price: 204,
      return_percent: 2,
      benchmark_symbol: "SPY",
      benchmark_return_percent: 0.7,
      alpha_percent: 1.3,
      maximum_favourable_excursion_percent: 2.5,
      maximum_drawdown_percent: -0.8,
      status: "POSITIVE",
      original_rank: 1,
      opportunity_score: 84.2,
      calibrated_confidence: 0.81,
      expected_return_percent: 3.2,
      evidence_coverage_percent: 88,
      eligible_for_execution: true,
      category: "EXECUTION_READY",
      sector: "Technology",
      historical_match_count: 8,
      measured_case_count: 6,
    },
  ],
  warnings: ["The selected horizon has fewer than 10 outcomes."],
};

vi.mock("@/hooks/useRankingValidation", () => ({
  useRankingValidation: () => ({
    data: report,
    isLoading: false,
    isError: false,
    error: null,
    isFetching: false,
    refetch: vi.fn(),
  }),
}));

describe("RankingValidationPage", () => {
  it("renders forward-return evidence and horizon controls", async () => {
    const user = userEvent.setup();

    render(<RankingValidationPage />);

    expect(screen.getByText("Ranking Validation")).toBeInTheDocument();
    expect(screen.getByText("Advisory only")).toBeInTheDocument();
    expect(screen.getByText("Does ranking add value?")).toBeInTheDocument();
    expect(screen.getByText("Score-band calibration")).toBeInTheDocument();
    expect(screen.getAllByText("AAPL").length).toBeGreaterThan(0);
    expect(screen.getByText("Latest measured outcomes")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "5D" }));
    expect(screen.getByRole("button", { name: "5D" })).toBeInTheDocument();
  });
});
