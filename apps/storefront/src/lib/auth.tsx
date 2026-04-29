'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';

interface AuthUser {
  token: string;
  email: string;
  first_name: string;
  last_name: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<AuthUser>;
  signup: (email: string, password: string, first_name: string, last_name: string) => Promise<AuthUser>;
  loginOrSignup: (email: string, password: string, first_name?: string, last_name?: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('kicks_auth');
      if (saved) setUser(JSON.parse(saved));
    } catch {}
  }, []);

  function persist(u: AuthUser) {
    setUser(u);
    localStorage.setItem('kicks_auth', JSON.stringify(u));
  }

  async function login(email: string, password: string): Promise<AuthUser> {
    const res = await fetch(`${API}/api/customer/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail ?? 'Login failed');
    const data = await res.json();

    const profile = await fetch(`${API}/api/customer/profile`, {
      headers: { Authorization: `Bearer ${data.token}` },
    });
    const p = await profile.json();
    const u: AuthUser = { token: data.token, email: p.email, first_name: p.first_name, last_name: p.last_name };
    persist(u);
    return u;
  }

  async function signup(email: string, password: string, first_name: string, last_name: string): Promise<AuthUser> {
    const res = await fetch(`${API}/api/customer/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, first_name, last_name }),
    });
    if (!res.ok) throw new Error((await res.json()).detail ?? 'Signup failed');
    const data = await res.json();
    const u: AuthUser = { token: data.token, email, first_name, last_name };
    persist(u);
    return u;
  }

  async function loginOrSignup(email: string, password: string, first_name = 'Guest', last_name = 'User'): Promise<AuthUser> {
    try {
      return await login(email, password);
    } catch {
      return await signup(email, password, first_name, last_name);
    }
  }

  function logout() {
    setUser(null);
    localStorage.removeItem('kicks_auth');
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, loginOrSignup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
