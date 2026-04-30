'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/lib/auth';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';
const WS_URL = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') ?? 'ws://localhost:3002';

interface Ticket { id: string; number: string; subject: string; status: string; created_at: string }
interface Message { id?: string; sender_type: 'customer' | 'staff'; sender_name: string; body: string; created_at: string; type?: string }

type View = 'closed' | 'auth' | 'list' | 'chat';

export default function ChatWidget() {
  const { user, loginOrSignup, logout } = useAuth();
  const [view, setView] = useState<View>('closed');

  // Auth form
  const [authForm, setAuthForm] = useState({ email: '', password: '', first_name: '', last_name: '' });
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Ticket list
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [ticketsLoading, setTicketsLoading] = useState(false);

  // New ticket form
  const [newSubject, setNewSubject] = useState('');
  const [newBody, setNewBody] = useState('');
  const [creating, setCreating] = useState(false);

  // Chat
  const [activeTicket, setActiveTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [staffOnline, setStaffOnline] = useState(false);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed' | 'error'>('closed');
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Open: go to list or auth
  function open() {
    if (user) {
      setView('list');
      loadTickets();
    } else {
      setView('auth');
    }
  }

  function close() {
    setView('closed');
    disconnectWs();
  }

  // Auth
  async function handleAuth(e: React.FormEvent) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    try {
      const loggedIn = await loginOrSignup(authForm.email, authForm.password, authForm.first_name || 'Guest', authForm.last_name || 'User');
      setView('list');
      loadTickets(loggedIn.token);  // use returned token, not stale state
    } catch (err: unknown) {
      setAuthError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setAuthLoading(false);
    }
  }

  // Ticket list
  async function loadTickets(token?: string) {
    const authToken = token ?? user?.token;
    if (!authToken) return;
    setTicketsLoading(true);
    try {
      const res = await fetch(`${API}/api/customer/support/tickets`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      const data = await res.json();
      setTickets(Array.isArray(data) ? data : []);
    } finally {
      setTicketsLoading(false);
    }
  }

  // Create ticket
  async function createTicket(e: React.FormEvent) {
    e.preventDefault();
    if (!user || !newSubject.trim()) return;
    setCreating(true);
    try {
      const res = await fetch(`${API}/api/customer/support/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user.token}` },
        body: JSON.stringify({ subject: newSubject, body: newBody }),
      });
      const ticket = await res.json();
      setNewSubject('');
      setNewBody('');
      openChat(ticket);
    } finally {
      setCreating(false);
    }
  }

  // Open existing ticket
  async function openChat(ticket: Ticket) {
    if (!user) return;
    setActiveTicket(ticket);
    setMessages([]);
    setView('chat');

    // Load history
    const res = await fetch(`${API}/api/customer/support/tickets/${ticket.id}/messages`, {
      headers: { Authorization: `Bearer ${user.token}` },
    });
    const data = await res.json();
    setMessages(data.messages ?? []);

    connectWs(ticket.id, user.token);
  }

  // WebSocket
  const connectWs = useCallback((ticketId: string, token: string) => {
    disconnectWs();
    setWsStatus('connecting');
    const ws = new WebSocket(`${WS_URL}/ws/chat/${ticketId}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => { if (wsRef.current === ws) setWsStatus('open'); };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'message') {
          setMessages(prev => [...prev, msg]);
        } else if (msg.type === 'joined' && msg.sender_type === 'staff') {
          setStaffOnline(true);
        } else if (msg.type === 'left' && msg.sender_type === 'staff') {
          setStaffOnline(false);
        }
      } catch {}
    };

    ws.onerror = () => { if (wsRef.current === ws) setWsStatus('error'); };
    ws.onclose = () => { if (wsRef.current === ws) { setStaffOnline(false); setWsStatus('closed'); } };
  }, []);

  function disconnectWs() {
    wsRef.current?.close();
    wsRef.current = null;
    setStaffOnline(false);
  }

  useEffect(() => () => disconnectWs(), []);

  function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ body: draft }));
    setDraft('');
  }

  // ── Render ───────────────────────────────────────────────────────────────

  if (view === 'closed') {
    return (
      <button
        onClick={open}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-black text-white rounded-full shadow-lg flex items-center justify-center text-2xl hover:bg-gray-800 transition-colors"
        aria-label="Open support chat"
      >
        💬
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 bg-white border border-gray-200 rounded-lg shadow-xl flex flex-col overflow-hidden" style={{ height: 480 }}>
      {/* Header */}
      <div className="bg-black text-white px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div>
          <p className="text-sm font-bold">KICKS Support</p>
          {view === 'chat' && (
            <p className="text-xs text-gray-400">
              {wsStatus === 'connecting' ? '○ Connecting…'
                : wsStatus === 'error' ? '⚠ Connection error'
                : wsStatus === 'closed' ? '○ Disconnected'
                : staffOnline ? '● Agent online' : '● Connected — waiting for agent…'}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {view === 'chat' && (wsStatus === 'error' || wsStatus === 'closed') && activeTicket && user && (
            <button onClick={() => connectWs(activeTicket.id, user.token)} className="text-gray-400 hover:text-white text-xs" title="Reconnect">↺</button>
          )}
          {view === 'chat' && (
            <button onClick={() => { disconnectWs(); setView('list'); loadTickets(); }} className="text-gray-400 hover:text-white text-xs">←</button>
          )}
          <button onClick={close} className="text-gray-400 hover:text-white text-lg leading-none">×</button>
        </div>
      </div>

      {/* Auth */}
      {view === 'auth' && (
        <form onSubmit={handleAuth} className="flex-1 p-4 space-y-3 overflow-auto">
          <p className="text-sm text-gray-600">Sign in to start a conversation.</p>
          <div className="grid grid-cols-2 gap-2">
            <input placeholder="First name" value={authForm.first_name}
              onChange={e => setAuthForm(p => ({ ...p, first_name: e.target.value }))}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:border-black" />
            <input placeholder="Last name" value={authForm.last_name}
              onChange={e => setAuthForm(p => ({ ...p, last_name: e.target.value }))}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:border-black" />
          </div>
          <input type="email" required placeholder="Email" value={authForm.email}
            onChange={e => setAuthForm(p => ({ ...p, email: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:border-black" />
          <input type="password" required placeholder="Password" value={authForm.password}
            onChange={e => setAuthForm(p => ({ ...p, password: e.target.value }))}
            className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:border-black" />
          {authError && <p className="text-red-600 text-xs">{authError}</p>}
          <button type="submit" disabled={authLoading}
            className="w-full bg-black text-white rounded py-2 text-sm font-medium disabled:opacity-50">
            {authLoading ? 'Please wait…' : 'Continue'}
          </button>
        </form>
      )}

      {/* Ticket list */}
      {view === 'list' && (
        <div className="flex-1 overflow-auto flex flex-col">
          {/* New conversation form */}
          <form onSubmit={createTicket} className="p-3 border-b border-gray-100 space-y-2 flex-shrink-0">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">New conversation</p>
            <input required placeholder="Subject" value={newSubject}
              onChange={e => setNewSubject(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:border-black" />
            <textarea placeholder="Describe your issue…" rows={2} value={newBody}
              onChange={e => setNewBody(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:border-black resize-none" />
            <button type="submit" disabled={creating}
              className="w-full bg-black text-white rounded py-1.5 text-sm font-medium disabled:opacity-50">
              {creating ? 'Starting…' : 'Start conversation'}
            </button>
          </form>

          {/* Past tickets */}
          <div className="flex-1 overflow-auto">
            {ticketsLoading ? (
              <p className="text-xs text-gray-400 p-3">Loading…</p>
            ) : tickets.length === 0 ? (
              <p className="text-xs text-gray-400 p-3">No previous conversations.</p>
            ) : (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 pt-3 pb-1">Previous conversations</p>
                {tickets.map(t => (
                  <button key={t.id} onClick={() => openChat(t)}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900 truncate">{t.subject}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-xs px-1.5 py-0.5 rounded-full ${t.status === 'open' ? 'bg-green-100 text-green-700' : t.status === 'resolved' ? 'bg-gray-100 text-gray-500' : 'bg-yellow-100 text-yellow-700'}`}>
                        {t.status}
                      </span>
                      <span className="text-xs text-gray-400">{t.number}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-gray-100 flex-shrink-0">
            <button onClick={() => { logout(); setView('auth'); }} className="text-xs text-gray-400 hover:text-gray-600">
              Sign out ({user?.email})
            </button>
          </div>
        </div>
      )}

      {/* Chat */}
      {view === 'chat' && activeTicket && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="px-3 py-1.5 border-b border-gray-100 flex-shrink-0">
            <p className="text-xs font-medium text-gray-700 truncate">{activeTicket.subject}</p>
            <p className="text-xs text-gray-400">{activeTicket.number}</p>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-auto p-3 space-y-3">
            {messages.length === 0 && (
              <p className="text-xs text-gray-400 text-center py-4">Waiting for a support agent to join…</p>
            )}
            {messages.map((m, i) => {
              const isMe = m.sender_type === 'customer';
              return (
                <div key={m.id ?? i} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}>
                  <p className="text-xs text-gray-400 mb-0.5">{m.sender_name}</p>
                  <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${isMe ? 'bg-black text-white' : 'bg-gray-100 text-gray-900'}`}>
                    {m.body}
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <form onSubmit={sendMessage} className="p-3 border-t border-gray-100 flex gap-2 flex-shrink-0">
            <input
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder="Type a message…"
              className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-black"
            />
            <button type="submit"
              disabled={!draft.trim()}
              className="bg-black text-white rounded px-3 py-1.5 text-sm disabled:opacity-40">
              ↑
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
