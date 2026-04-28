'use client';

import { useEffect, useState } from 'react';
import { useAuth, authHeaders } from '@/lib/auth';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';

interface KPIs {
  total_orders: number;
  revenue: number;
  open_tickets: number;
  total_customers: number;
  pending_orders: number;
  urgent_tickets: number;
}

function KpiCard({ label, value, sub, warn }: { label: string; value: string | number; sub?: string; warn?: boolean }) {
  return (
    <div className={`bg-white rounded border p-5 ${warn ? 'border-red-200' : 'border-gray-200'}`}>
      <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${warn ? 'text-red-600' : 'text-gray-900'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const { token } = useAuth();
  const [kpis, setKpis] = useState<KPIs | null>(null);

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/admin/dashboard`, { headers: authHeaders(token) })
      .then(r => r.json())
      .then(setKpis);
  }, [token]);

  if (!kpis) {
    return (
      <div className="p-8">
        <p className="text-gray-400 text-sm">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        <KpiCard label="Total Revenue" value={`€${kpis.revenue.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} sub="shipped + delivered orders" />
        <KpiCard label="Total Orders" value={kpis.total_orders.toLocaleString()} />
        <KpiCard label="Pending Orders" value={kpis.pending_orders} warn={kpis.pending_orders > 20} sub="awaiting confirmation" />
        <KpiCard label="Customers" value={kpis.total_customers.toLocaleString()} />
        <KpiCard label="Open Tickets" value={kpis.open_tickets} warn={kpis.open_tickets > 10} />
        <KpiCard label="Urgent Tickets" value={kpis.urgent_tickets} warn={kpis.urgent_tickets > 0} sub="require immediate attention" />
      </div>

      <div className="bg-white border border-gray-200 rounded p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Quick Links</h2>
        <div className="flex flex-wrap gap-2">
          <a href="/orders?status=pending" className="btn-secondary text-xs">Pending orders</a>
          <a href="/support?status=open" className="btn-secondary text-xs">Open tickets</a>
          <a href="/support?priority=urgent" className="btn-secondary text-xs">Urgent tickets</a>
          <a href="/products" className="btn-secondary text-xs">Product catalog</a>
          <a href="/api-keys" className="btn-secondary text-xs">API keys</a>
        </div>
      </div>
    </div>
  );
}
