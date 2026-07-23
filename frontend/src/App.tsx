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
