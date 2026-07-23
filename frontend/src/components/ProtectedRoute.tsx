import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Redirect } from "wouter";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/AppShell";

interface ProtectedRouteProps {
  component: React.ComponentType;
  title: string;
}

export function ProtectedRoute({
  component: Component,
  title,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm font-medium tracking-wide uppercase">
            Initializing Context...
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Redirect to="/login" />;
  }

  return (
    <AppShell title={title}>
      <Component />
    </AppShell>
  );
}
