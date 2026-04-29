'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth, authHeaders } from '@/lib/auth';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';
const WS_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002').replace(/^http/, 'ws');

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
  id: string; number: string; subject: string; status: string;
  priority: string; created_at: string; customer_id: string;
}

interface ChatMsg {
  id?: string; sender_type: string; sender_name: string;
  body: string; created_at: string; internal?: boolean; type?: string;
}

const STATUSES = ['', 'open', 'in_progress', 'waiting_customer', 'resolved', 'closed'];

export default function SupportPage() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [status, setStatus] = useState(searchParams.get('status') ?? '');
  const [loading, setLoading] = useState(true);

  // Chat panel
  const [activeTicket, setActiveTicket] = useState<{ id: string; number: string; subject: string; customer_name: string } | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [draft, setDraft] = useState('');
  const [wsReady, setWsReady] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

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

  // Open chat for a ticket
  async function openChat(ticket: Ticket) {
    closeChat();
    if (!token) return;

    const res = await fetch(`${API}/api/admin/support/tickets/${ticket.id}/messages`, {
      headers: authHeaders(token),
    });
    const data = await res.json();
    setActiveTicket({ id: ticket.id, number: ticket.number, subject: ticket.subject, customer_name: data.customer_name ?? 'Customer' });
    setMessages(data.messages ?? []);
    connectWs(ticket.id);
  }

  const connectWs = useCallback((ticketId: string) => {
    if (!token) return;
    const ws = new WebSocket(`${WS_URL}/ws/chat/${ticketId}?token=${token}`);
    wsRef.current = ws;
    ws.onopen = () => setWsReady(true);
    ws.onclose = () => setWsReady(false);
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'message') {
        setMessages(prev => [...prev, msg]);
      }
      // Also refresh ticket list to update statuses
      load(status);
    };
  }, [token, status]);

  function closeChat() {
    wsRef.current?.close();
    wsRef.current = null;
    setWsReady(false);
    setActiveTicket(null);
    setMessages([]);
  }

  useEffect(() => () => { wsRef.current?.close(); }, []);

  function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ body: draft }));
    setDraft('');
  }

  return (
    <div className="flex h-full">
      {/* Ticket list */}
      <div className={`flex flex-col ${activeTicket ? 'w-1/2 border-r border-gray-200' : 'flex-1'} p-6 overflow-auto`}>
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-gray-900">Support Tickets</h1>
          <div className="flex flex-wrap gap-1.5">
            {STATUSES.map(s => (
              <button key={s} onClick={() => changeStatus(s)}
                className={`text-xs px-2.5 py-1 rounded border ${status === s ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'}`}>
                {s || 'All'}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase">#</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase">Subject</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase">Priority</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-500 uppercase">Chat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">Loading…</td></tr>
              ) : tickets.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">No tickets</td></tr>
              ) : tickets.map(ticket => (
                <tr key={ticket.id}
                  className={`hover:bg-gray-50 cursor-pointer ${activeTicket?.id === ticket.id ? 'bg-blue-50' : ''}`}
                  onClick={() => openChat(ticket)}>
                  <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{ticket.number}</td>
                  <td className="px-4 py-2.5 text-gray-900 max-w-xs truncate">{ticket.subject}</td>
                  <td className="px-4 py-2.5">
                    <span className={`badge ${STATUS_COLORS[ticket.status] ?? 'bg-gray-100 text-gray-600'}`}>
                      {ticket.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`badge ${PRIORITY_COLORS[ticket.priority] ?? 'bg-gray-100 text-gray-600'}`}>
                      {ticket.priority}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs ${activeTicket?.id === ticket.id && wsReady ? 'text-green-600 font-medium' : 'text-gray-400'}`}>
                      {activeTicket?.id === ticket.id && wsReady ? '● live' : 'Open →'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-400 mt-2">{tickets.length} tickets (max 50)</p>
      </div>

      {/* Chat panel */}
      {activeTicket && (
        <div className="w-1/2 flex flex-col overflow-hidden">
          {/* Chat header */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-gray-200 flex-shrink-0 bg-white">
            <div>
              <p className="text-sm font-semibold text-gray-900">{activeTicket.subject}</p>
              <p className="text-xs text-gray-500">
                {activeTicket.number} · {activeTicket.customer_name}
                {wsReady && <span className="ml-2 text-green-600 font-medium">● connected</span>}
              </p>
            </div>
            <button onClick={closeChat} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-auto p-4 space-y-3 bg-gray-50">
            {messages.length === 0 && (
              <p className="text-xs text-gray-400 text-center py-8">No messages yet.</p>
            )}
            {messages.map((m, i) => {
              const isStaff = m.sender_type === 'staff';
              return (
                <div key={m.id ?? i} className={`flex flex-col ${isStaff ? 'items-end' : 'items-start'}`}>
                  <p className="text-xs text-gray-400 mb-0.5">{m.sender_name}</p>
                  <div className={`max-w-xs rounded-lg px-3 py-2 text-sm ${isStaff ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-900'} ${m.internal ? 'border-dashed border-yellow-400' : ''}`}>
                    {m.body}
                    {m.internal && <span className="ml-1 text-xs text-yellow-300">(internal)</span>}
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <form onSubmit={sendMessage} className="p-3 border-t border-gray-200 flex gap-2 flex-shrink-0 bg-white">
            <input
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder={wsReady ? 'Reply to customer…' : 'Connecting…'}
              disabled={!wsReady}
              className="flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-black disabled:bg-gray-50"
            />
            <button type="submit" disabled={!draft.trim() || !wsReady}
              className="btn-primary text-sm px-3 disabled:opacity-40">
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
