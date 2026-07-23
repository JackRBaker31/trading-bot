import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import {
  apiClient,
  setCsrfToken,
  getCsrfToken,
  setSessionToken,
  setSessionExpiredHandler,
} from "@/lib/api-client";
import { AuthUser, LoginResponse } from "@/lib/types";
import { useLocation } from "wouter";

interface AuthState {
  user: AuthUser | null;
  csrfToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login(username: string, password: string): Promise<void>;
  logout(): Promise<void>;
  refreshSession(): Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [, setLocation] = useLocation();

  const refreshSession = useCallback(async () => {
    try {
      const data = await apiClient.get<{
        user_id: string;
        username: string;
        role: string;
      }>("/auth/me");
      setUser(data);
    } catch (err) {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  // Register a handler so api-client can trigger a redirect when any request
  // receives a 401 (session expired mid-use).
  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null);
      setLocation("/login?expired=1");
    });
    return () => setSessionExpiredHandler(null);
  }, [setLocation]);

  const login = async (username: string, password: string) => {
    const response = await apiClient.post<LoginResponse>("/auth/login", {
      username,
      password,
    });
    // Store both tokens in memory. The session token is sent as X-Session-Token
    // on every request, bypassing SameSite=Lax cookie restrictions on cross-origin POSTs.
    setCsrfToken(response.csrf_token);
    setSessionToken(response.session_token);
    setUser(response.user);
  };

  const logout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch (e) {
      // Ignore errors on logout
    } finally {
      setCsrfToken(null);
      setSessionToken(null);
      setUser(null);
      setLocation("/login");
    }
  };

  const value = {
    user,
    csrfToken: getCsrfToken(),
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
