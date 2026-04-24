"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api } from "./api";

interface AuthCtx {
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, nombre: string) => Promise<void>;
  logout: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const t = localStorage.getItem("cmx_token");
    setToken(t);
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.auth.login(email, password);
    localStorage.setItem("cmx_token", res.access_token);
    setToken(res.access_token);
    router.push("/chat");
  };

  const register = async (email: string, password: string, nombre: string) => {
    const res = await api.auth.register(email, password, nombre);
    localStorage.setItem("cmx_token", res.access_token);
    setToken(res.access_token);
    router.push("/chat");
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch {
      // Si el token ya expiró o hay error de red, igual borramos localmente
    } finally {
      localStorage.removeItem("cmx_token");
      setToken(null);
      router.push("/login");
    }
  };

  return <Ctx.Provider value={{ token, loading, login, register, logout }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
