import React, { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useLocation, useSearch } from "wouter";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, AlertCircle, Clock } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const [, setLocation] = useLocation();
  const search = useSearch();
  const sessionExpired = new URLSearchParams(search).get("expired") === "1";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login(username, password);
      setLocation("/operations");
    } catch (err: any) {
      setError(err.message || "Invalid credentials");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center relative overflow-hidden gap-8">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-background to-background pointer-events-none" />

      {/* Logo above the card */}
      <div className="relative z-10 flex flex-col items-center gap-4">
        <img
          src="/kairo-logo.png"
          alt="Kairo"
          className="max-w-[560px] w-full object-contain"
        />
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border border-[#D4AF37]/50 text-[#D4AF37] bg-[#D4AF37]/10 uppercase tracking-wider">
          Demo Platform
        </span>
      </div>

      {/* Login card with gold glow border */}
      <Card
        className="w-full max-w-md bg-card/90 backdrop-blur relative z-10 shadow-2xl"
        style={{
          border: "1px solid rgba(212,175,55,0.55)",
          boxShadow: "0 0 32px 4px rgba(212,175,55,0.18), 0 0 8px 1px rgba(212,175,55,0.25), 0 20px 60px rgba(0,0,0,0.5)",
        }}
      >
        <CardHeader className="pb-4 pt-8 text-center" />
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {sessionExpired && !error && (
              <Alert className="bg-amber-500/10 border-amber-500/30 text-amber-200">
                <Clock className="h-4 w-4 text-amber-400" />
                <AlertDescription data-testid="text-session-expired">
                  Your session expired. Please log in again.
                </AlertDescription>
              </Alert>
            )}
            {error && (
              <Alert
                variant="destructive"
                className="bg-destructive/10 border-destructive/20 text-destructive-foreground"
              >
                <AlertCircle className="h-4 w-4" />
                <AlertDescription data-testid="text-error">
                  {error}
                </AlertDescription>
              </Alert>
            )}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label
                  htmlFor="username"
                  className="text-xs uppercase tracking-wider text-muted-foreground"
                >
                  Username
                </Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="bg-input/50 border-border focus-visible:ring-primary h-11"
                  data-testid="input-username"
                />
              </div>
              <div className="space-y-2">
                <Label
                  htmlFor="password"
                  className="text-xs uppercase tracking-wider text-muted-foreground"
                >
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-input/50 border-border focus-visible:ring-primary h-11"
                  data-testid="input-password"
                />
              </div>
            </div>
            <Button
              type="submit"
              className="w-full h-11 font-medium tracking-wide uppercase text-xs"
              disabled={isSubmitting}
              data-testid="button-login"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                "Access Terminal"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
