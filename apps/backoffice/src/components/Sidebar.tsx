'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';

const nav = [
  { href: '/dashboard', label: 'Dashboard', icon: '▦' },
  { href: '/orders', label: 'Orders', icon: '📦' },
  { href: '/support', label: 'Support', icon: '🎫' },
  { href: '/products', label: 'Products', icon: '👟' },
  { href: '/customers', label: 'Customers', icon: '👤' },
  { href: '/api-keys', label: 'API Keys', icon: '🔑' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-56 bg-gray-900 min-h-screen flex flex-col">
      <div className="px-4 py-5 border-b border-gray-700">
        <p className="text-white font-bold text-sm">KICKS</p>
        <p className="text-gray-400 text-xs">Back Office</p>
      </div>

      <nav className="flex-1 px-2 py-4 space-y-0.5">
        {nav.map(({ href, label, icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors ${
                active
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      {user && (
        <div className="px-4 py-4 border-t border-gray-700">
          <p className="text-gray-300 text-xs font-medium truncate">{user.first_name} {user.last_name}</p>
          <p className="text-gray-500 text-xs truncate mb-2">{user.email}</p>
          <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
