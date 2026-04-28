'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth, authHeaders } from '@/lib/auth';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
};

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-blue-100 text-blue-800',
  waiting_customer: 'bg-purple-100 text-purple-800',
  resolved: 'bg-green-100 text-green-700',
  closed: 'bg-gray-100 text-gray-500',
};

interface Ticket {
  id: string;
  number: string;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
  customer_id: string;
}

const STATUSES = ['', 'open', 'in_progress', 'waiting_customer', 'resolved', 'closed'];

export default function SupportPage() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [status, setStatus] = useState(searchParams.get('status') ?? '');
  const [loading, setLoading] = useState(true);

  function load(s: string) {
    if (!token) return;
    setLoading(true);
    const qs = s ? `?status=${s}&limit=50` : '?limit=50';
    fetch(`${API}/api/admin/support/tickets${qs}`, { headers: authHeaders(token) })
      .then(r => r.json())
      .then(data => { setTickets(Array.isArray(data) ? data : []); setLoading(false); });
  }

  useEffect(() => { load(status); }, [token, status]);

  function changeStatus(s: string) {
    setStatus(s);
    router.replace(s ? `/support?status=${s}` : '/support');
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Support Tickets</h1>
        <div className="flex flex-wrap gap-2">
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
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">#</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Subject</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Priority</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">Loading...</td></tr>
            ) : tickets.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">No tickets found</td></tr>
            ) : tickets.map(ticket => (
              <tr key={ticket.id} className="table-row-hover">
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{ticket.number}</td>
                <td className="px-4 py-3 text-gray-900 max-w-xs truncate">{ticket.subject}</td>
                <td className="px-4 py-3">
                  <span className={`badge ${STATUS_COLORS[ticket.status] ?? 'bg-gray-100 text-gray-600'}`}>
                    {ticket.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`badge ${PRIORITY_COLORS[ticket.priority] ?? 'bg-gray-100 text-gray-600'}`}>
                    {ticket.priority}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(ticket.created_at).toLocaleDateString('fr-FR')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-400 mt-3">{tickets.length} tickets shown (max 50)</p>
    </div>
  );
}
