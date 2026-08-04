import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "@/test/handlers";
import ResearchLabPage from "@/pages/ResearchLabPage";

test("renders evidence-backed research findings and safe experiments", async () => {
  server.use(http.get("http://127.0.0.1:8000/api/research-lab/brief", () => HttpResponse.json({
    generated_at:"2026-08-04T10:00:00+00:00", period:{start:"x",end:"y",hours:168}, status:"EVIDENCE_BUILDING", trading_impact:"NONE", headline:"Evidence is maturing", summary:"Summary",
    evidence:{shadow_decisions:88,measured_1d_decisions:83,directional_success_percent:36.14,profitable_after_cost_percent:33.73,calibration_sample_size:83,healthy_completion_percent:99},
    findings:[{kind:"PERFORMANCE",title:"One-day shadow evidence",statement:"83 measured",sample_size:83,confidence:"LIMITED"}],
    suggested_experiments:[{experiment_id:"EVIDENCE-001",title:"Continue unchanged evidence collection",hypothesis:"Clean baseline",status:"RECOMMENDED",risk:"LOW",required_sample:150,current_sample:83,automatic_change:false}],
    sector_leaders:[],confidence_buckets:[],timeline:[],methodology:{deterministic:true,external_language_model:false,automatic_model_changes:false,minimum_serious_review_sample:150,source:"KAIRO SQLite"}
  })));
  render(<QueryClientProvider client={new QueryClient()}><ResearchLabPage /></QueryClientProvider>);
  expect(await screen.findByText("AI Research Lab")).toBeInTheDocument();
  expect(await screen.findByText("One-day shadow evidence")).toBeInTheDocument();
  expect(await screen.findByText("Continue unchanged evidence collection")).toBeInTheDocument();
  expect(screen.getByText("NONE")).toBeInTheDocument();
});
