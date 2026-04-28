'use client';

import { createContext, useContext, useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';

interface StaffUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  status: string;
}

interface AuthCtx {
  user: StaffUser | null;
  token: string;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthCtx>({
  user: null, token: '', login: async () => {}, logout: () => {}, loading: true,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState('');
  const [user, setUser] = useState<StaffUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('staff_token');
    if (stored) {
      setToken(stored);
      fetchMe(stored).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function fetchMe(t: string) {
    const res = await fetch(`${API}/api/admin/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    });
    if (res.ok) {
      setUser(await res.json());
    } else {
      localStorage.removeItem('staff_token');
      setToken('');
      setUser(null);
    }
  }

  async function login(email: string, password: string) {
    const res = await fetch(`${API}/api/admin/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Login failed');
    }
    const data = await res.json();
    localStorage.setItem('staff_token', data.token);
    setToken(data.token);
    await fetchMe(data.token);
  }

  function logout() {
    localStorage.removeItem('staff_token');
    setToken('');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
}
