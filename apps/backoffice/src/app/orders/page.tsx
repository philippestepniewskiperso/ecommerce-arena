'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth, authHeaders } from '@/lib/auth';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  shipped: 'bg-indigo-100 text-indigo-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-gray-100 text-gray-600',
  refunded: 'bg-red-100 text-red-800',
};

interface Order {
  id: string;
  number: string;
  status: string;
  total: number;
  currency: string;
  placed_at: string;
  customer_id: string;
}

const STATUSES = ['', 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled', 'refunded'];

export default function OrdersPage() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [status, setStatus] = useState(searchParams.get('status') ?? '');
  const [loading, setLoading] = useState(true);

  function load(s: string) {
    if (!token) return;
    setLoading(true);
    const qs = s ? `?status=${s}&limit=50` : '?limit=50';
    fetch(`${API}/api/admin/orders${qs}`, { headers: authHeaders(token) })
      .then(r => r.json())
      .then(data => { setOrders(Array.isArray(data) ? data : []); setLoading(false); });
  }

  useEffect(() => { load(status); }, [token, status]);

  function changeStatus(s: string) {
    setStatus(s);
    router.replace(s ? `/orders?status=${s}` : '/orders');
  }

  async function updateStatus(orderId: string, newStatus: string) {
    await fetch(`${API}/api/admin/orders/${orderId}/status`, {
      method: 'PATCH',
      headers: authHeaders(token),
      body: JSON.stringify({ status: newStatus }),
    });
    load(status);
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Orders</h1>
        <div className="flex gap-2">
          {STATUSES.map(s => (
            <button
              key={s}
              onClick={() => changeStatus(s)}
              className={`text-xs px-3 py-1.5 rounded border ${status === s ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'}`}
            >
              {s || 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Order</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Total</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Placed</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">Loading...</td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">No orders found</td></tr>
            ) : orders.map(order => (
              <tr key={order.id} className="table-row-hover">
                <td className="px-4 py-3 font-mono text-xs text-gray-900">{order.number}</td>
                <td className="px-4 py-3">
                  <span className={`badge ${STATUS_COLORS[order.status] ?? 'bg-gray-100 text-gray-600'}`}>
                    {order.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-700">€{Number(order.total).toFixed(2)}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(order.placed_at).toLocaleDateString('fr-FR')}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5">
                    {order.status === 'pending' && (
                      <button onClick={() => updateStatus(order.id, 'confirmed')} className="btn-secondary text-xs py-1">Confirm</button>
                    )}
                    {order.status === 'confirmed' && (
                      <button onClick={() => updateStatus(order.id, 'shipped')} className="btn-primary text-xs py-1">Ship</button>
                    )}
                    {order.status === 'shipped' && (
                      <button onClick={() => updateStatus(order.id, 'delivered')} className="btn-primary text-xs py-1">Delivered</button>
                    )}
                    {['pending', 'confirmed'].includes(order.status) && (
                      <button onClick={() => updateStatus(order.id, 'cancelled')} className="btn-danger text-xs py-1">Cancel</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-400 mt-3">{orders.length} orders shown (max 50)</p>
    </div>
  );
}
