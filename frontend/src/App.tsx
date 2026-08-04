import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch, Router as WouterRouter } from "wouter";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";

import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import ResearchPage from "@/pages/ResearchPage";
import NewsPage from "@/pages/NewsPage";
import PortfolioPage from "@/pages/PortfolioPage";
import OrdersPage from "@/pages/OrdersPage";
import RiskPage from "@/pages/RiskPage";
import PaperTradingPage from "@/pages/PaperTradingPage";
import JobsPage from "@/pages/JobsPage";
import AuditPage from "@/pages/AuditPage";
import ShadowIntelligencePage from "@/pages/ShadowIntelligencePage";
import SchedulesPage from "@/pages/SchedulesPage";
import OperationsPage from "@/pages/OperationsPage";
import CopilotPage from "@/pages/CopilotPage";
import PerformanceIntelligencePage from "@/pages/PerformanceIntelligencePage";
import DecisionExplainabilityPage from "@/pages/DecisionExplainabilityPage";
import OpportunityRankingPage from "@/pages/OpportunityRankingPage";
import RankingValidationPage from "@/pages/RankingValidationPage";
import UniverseGovernancePage from "@/pages/UniverseGovernancePage";
import ResearchLabPage from "@/pages/ResearchLabPage";
import ConfidenceCalibrationPage from "@/pages/ConfidenceCalibrationPage";
import FeatureContributionsPage from "@/pages/FeatureContributionsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold bg-gradient-to-br from-[#D4AF37] to-[#C0C0C0] bg-clip-text text-transparent">
          404
        </h1>
        <p className="uppercase tracking-widest text-muted-foreground text-sm">
          System Route Not Found
        </p>
      </div>
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/login" component={LoginPage} />
      <Route
        path="/"
        component={() => {
          window.location.href = "/operations";
          return null;
        }}
      />
      <Route path="/operations">
        {() => (
          <ProtectedRoute
            component={OperationsPage}
            title="Operations Centre"
          />
        )}
      </Route>
      <Route path="/copilot">
        {() => (
          <ProtectedRoute
            component={CopilotPage}
            title="KAIRO Copilot"
          />
        )}
      </Route>
      <Route path="/research-lab">
        {() => (
          <ProtectedRoute component={ResearchLabPage} title="AI Research Lab" />
        )}
      </Route>
      <Route path="/confidence-calibration">
        {() => (
          <ProtectedRoute component={ConfidenceCalibrationPage} title="Confidence Calibration" />
        )}
      </Route>
      <Route path="/feature-contributions">
        {() => (
          <ProtectedRoute component={FeatureContributionsPage} title="Feature Contributions" />
        )}
      </Route>
      <Route path="/performance">
        {() => (
          <ProtectedRoute
            component={PerformanceIntelligencePage}
            title="Performance Intelligence"
          />
        )}
      </Route>
      <Route path="/decision-explainability">
        {() => (
          <ProtectedRoute
            component={DecisionExplainabilityPage}
            title="Decision Explainability"
          />
        )}
      </Route>
      <Route path="/opportunity-ranking">
        {() => (
          <ProtectedRoute
            component={OpportunityRankingPage}
            title="Opportunity Ranking"
          />
        )}
      </Route>
      <Route path="/ranking-validation">
        {() => (
          <ProtectedRoute
            component={RankingValidationPage}
            title="Ranking Validation"
          />
        )}
      </Route>
      <Route path="/universe-governance">
        {() => (
          <ProtectedRoute
            component={UniverseGovernancePage}
            title="Universe Governance"
          />
        )}
      </Route>
      <Route path="/dashboard">
        {() => (
          <ProtectedRoute component={DashboardPage} title="System Overview" />
        )}
      </Route>
      <Route path="/research">
        {() => (
          <ProtectedRoute
            component={ResearchPage}
            title="AI Research Operations"
          />
        )}
      </Route>
      <Route path="/news">
        {() => (
          <ProtectedRoute
            component={NewsPage}
            title="News Signals & Outcomes"
          />
        )}
      </Route>
      <Route path="/portfolio">
        {() => (
          <ProtectedRoute
            component={PortfolioPage}
            title="Portfolio Positions"
          />
        )}
      </Route>
      <Route path="/orders">
        {() => (
          <ProtectedRoute component={OrdersPage} title="Order Management" />
        )}
      </Route>
      <Route path="/risk">
        {() => <ProtectedRoute component={RiskPage} title="Risk Controls" />}
      </Route>
      <Route path="/paper-trading">
        {() => (
          <ProtectedRoute
            component={PaperTradingPage}
            title="Paper Trading Worker"
          />
        )}
      </Route>
      <Route path="/jobs">
        {() => <ProtectedRoute component={JobsPage} title="Background Jobs" />}
      </Route>
      <Route path="/audit">
        {() => (
          <ProtectedRoute component={AuditPage} title="System Audit Log" />
        )}
      </Route>
      <Route path="/shadow">
        {() => (
          <ProtectedRoute
            component={ShadowIntelligencePage}
            title="Shadow Intelligence"
          />
        )}
      </Route>
      <Route path="/schedules">
        {() => (
          <ProtectedRoute
            component={SchedulesPage}
            title="Automation Scheduler"
          />
        )}
      </Route>

      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
        <AuthProvider>
          <TooltipProvider>
            <Router />
            <Toaster />
          </TooltipProvider>
        </AuthProvider>
      </WouterRouter>
    </QueryClientProvider>
  );
}

export default App;
