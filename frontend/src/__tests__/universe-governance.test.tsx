import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import UniverseGovernancePage from "@/pages/UniverseGovernancePage";
import { render } from "@/test/test-utils";

const refetch = vi.fn();

vi.mock("@/hooks/useUniverseGovernance", () => ({
  useUniverseGovernance: () => ({
    data: {
      generated_at: "2026-07-29T12:00:00Z",
      governance_version: "KAIRO-UGOV-1.0",
      source_path: "data/watchlists/core_universe.txt",
      current_version: {
        version_id: "KAIRO-U-106-ABCDEF",
        checksum: "abcdef123456",
        created_at: "2026-07-29T08:00:00Z",
        source_path: "data/watchlists/core_universe.txt",
        symbol_count: 106,
        groups: { Technology: ["AAPL", "MSFT"] },
        symbols: ["AAPL", "MSFT"],
        previous_version_id: null,
        added_symbols: ["AAPL", "MSFT"],
        removed_symbols: [],
      },
      previous_version: null,
      version_count: 1,
      group_summaries: [
        {
          name: "Technology",
          symbol_count: 20,
          share_percent: 18.87,
          symbols: ["AAPL", "MSFT", "NVDA"],
        },
        {
          name: "Healthcare",
          symbol_count: 10,
          share_percent: 9.43,
          symbols: ["LLY", "UNH"],
        },
      ],
      duplicate_symbols: [],
      invalid_symbols: [],
      eligibility_status: "VALID",
      cached_symbol_count: 80,
      uncached_symbol_count: 26,
      cache_coverage_percent: 75.47,
      cached_symbols: ["AAPL"],
      uncached_symbols: ["LLY"],
      estimated_live_requests: 26,
      daily_request_budget: 750,
      estimated_budget_percent: 3.47,
      latest_cycle_coverage: {
        coverage_id: 1,
        captured_at: "2026-07-29T11:35:00Z",
        source: "INTELLIGENCE_CYCLE",
        version_id: "KAIRO-U-106-ABCDEF",
        requested_count: 106,
        processed_count: 106,
        skipped_count: 0,
        coverage_percent: 100,
        processed_symbols: ["AAPL", "MSFT"],
        skipped_symbols: [],
      },
      recent_cycle_coverage: [
        {
          coverage_id: 1,
          captured_at: "2026-07-29T11:35:00Z",
          source: "INTELLIGENCE_CYCLE",
          version_id: "KAIRO-U-106-ABCDEF",
          requested_count: 106,
          processed_count: 106,
          skipped_count: 0,
          coverage_percent: 100,
          processed_symbols: ["AAPL", "MSFT"],
          skipped_symbols: [],
        },
      ],
      versions: [
        {
          version_id: "KAIRO-U-106-ABCDEF",
          checksum: "abcdef123456",
          created_at: "2026-07-29T08:00:00Z",
          source_path: "data/watchlists/core_universe.txt",
          symbol_count: 106,
          groups: { Technology: ["AAPL", "MSFT"] },
          symbols: ["AAPL", "MSFT"],
          previous_version_id: null,
          added_symbols: ["AAPL", "MSFT"],
          removed_symbols: [],
        },
      ],
      rank_comparability_warning: null,
      warnings: [],
    },
    isLoading: false,
    isError: false,
    error: null,
    isFetching: false,
    refetch,
  }),
}));

describe("UniverseGovernancePage", () => {
  it("renders universe version, coverage and sector governance", async () => {
    const user = userEvent.setup();

    render(<UniverseGovernancePage />);

    expect(screen.getByText("Universe Governance")).toBeInTheDocument();
    expect(screen.getAllByText("KAIRO-U-106-ABCDEF").length).toBeGreaterThan(0);
    expect(screen.getByText("Sector and universe distribution")).toBeInTheDocument();
    expect(screen.getByText("Intelligence Cycle universe coverage")).toBeInTheDocument();
    expect(screen.getByText("Technology")).toBeInTheDocument();
    expect(screen.getAllByText("100.0%").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: /Refresh governance/i }));
    expect(refetch).toHaveBeenCalled();
  });
});
