"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api";

type AuthState = {
  loading: boolean;
  email: string | null;
  balance: number | null;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState<string | null>(null);
  const [balance, setBalance] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    const me = await api.me();
    if (me.authenticated) {
      setEmail(me.email);
      setBalance(me.balance);
    } else {
      setEmail(null);
      setBalance(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialSession() {
      try {
        await refresh();
      } catch {
        // Couldn't reach the backend on first load - treat as logged out;
        // useRequireAuth() will bounce protected pages to /login. Without
        // this catch, a down backend would surface as an unhandled promise
        // rejection instead of just showing the login page.
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadInitialSession();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const logout = useCallback(async () => {
    await api.logout();
    setEmail(null);
    setBalance(null);
  }, []);

  return (
    <AuthContext.Provider value={{ loading, email, balance, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return context;
}
