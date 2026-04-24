"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import WelcomeBanner from "@/components/onboarding/WelcomeBanner";
import { useAuth } from "@/lib/auth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token) router.replace("/login");
  }, [token, loading, router]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#0a0f0a" }}>
      <div className="text-green-500 text-sm">Cargando...</div>
    </div>
  );

  if (!token) return null;

  return (
    <div className="flex min-h-screen" style={{ background: "#0a0f0a" }}>
      <WelcomeBanner />
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">{children}</main>
    </div>
  );
}
