import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const TOKEN_KEY = "str_token";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const clearAuth = useCallback(() => {
    setToken("");
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
  }, []);

  const refreshUser = useCallback(
    async (overrideToken) => {
      const activeToken = overrideToken ?? token;
      if (!activeToken) return null;
      try {
        const resp = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${activeToken}` },
        });
        if (!resp.ok) throw new Error("Failed to load profile");
        const data = await resp.json();
        setUser(data);
        setError(null);
        return data;
      } catch (err) {
        setError(err.message);
        clearAuth();
        return null;
      }
    },
    [token, clearAuth]
  );

  const login = useCallback(
    async (email, password) => {
      const resp = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || "Login failed");
      }
      const data = await resp.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      await refreshUser(data.access_token);
    },
    [refreshUser]
  );

  const signup = useCallback(async (payload) => {
    const resp = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || "Signup failed");
    }
    // Auto-login after signup
    await login(payload.email, payload.password);
  }, [login]);

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  useEffect(() => {
    const initialize = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      await refreshUser(token);
      setLoading(false);
    };
    initialize();
  }, [token, refreshUser]);

  const value = useMemo(
    () => ({ token, user, loading, error, login, signup, logout, refreshUser }),
    [token, user, loading, error, login, signup, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
