'use client';

import { useEffect, useState } from 'react';
import { useAuth, authHeaders } from '@/lib/auth';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';

interface ApiKey {
  id: string;
  name: string;
  scopes: string[];
  created_at: string;
  last_used_at: string | null;
}

export default function ApiKeysPage() {
  const { token } = useAuth();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newScopes, setNewScopes] = useState('orders.read,customers.read');
  const [createdKey, setCreatedKey] = useState('');

  function load() {
    if (!token) return;
    fetch(`${API}/api/admin/api-keys`, { headers: authHeaders(token) })
      .then(r => r.json())
      .then(data => { setKeys(Array.isArray(data) ? data : []); setLoading(false); });
  }

  useEffect(() => { load(); }, [token]);

  async function createKey() {
    if (!newName.trim()) return;
    const scopes = newScopes.split(',').map(s => s.trim()).filter(Boolean);
    const res = await fetch(`${API}/api/admin/api-keys`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify({ name: newName, scopes }),
    });
    const data = await res.json();
    setCreatedKey(data.key ?? '');
    setCreating(false);
    setNewName('');
    load();
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">API Keys</h1>
        <button onClick={() => setCreating(true)} className="btn-primary">Create key</button>
      </div>

      {createdKey && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded p-4">
          <p className="text-sm font-medium text-green-800 mb-1">Key created — save it now, shown only once:</p>
          <code className="text-xs font-mono text-green-900 break-all">{createdKey}</code>
          <button onClick={() => setCreatedKey('')} className="mt-2 block text-xs text-green-600 hover:text-green-800">Dismiss</button>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Scopes</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Last used</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400 text-sm">Loading...</td></tr>
            ) : keys.length === 0 ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400 text-sm">No API keys</td></tr>
            ) : keys.map(k => (
              <tr key={k.id}>
                <td className="px-4 py-3 font-medium text-gray-900">{k.name}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {k.scopes.map(s => (
                      <span key={s} className="badge bg-blue-50 text-blue-700">{s}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(k.created_at).toLocaleDateString('fr-FR')}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString('fr-FR') : 'Never'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {creating && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded border border-gray-200 shadow-xl p-6 w-full max-w-sm">
            <h2 className="font-bold text-gray-900 mb-4">Create API key</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Name</label>
                <input
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  placeholder="my-agent"
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Scopes (comma-separated)</label>
                <input
                  value={newScopes}
                  onChange={e => setNewScopes(e.target.value)}
                  placeholder="orders.read,customers.read"
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900"
                />
                <p className="text-xs text-gray-400 mt-1">e.g. orders.read, orders.write, support.read, support.write</p>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={createKey} className="btn-primary flex-1">Create</button>
              <button onClick={() => setCreating(false)} className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
