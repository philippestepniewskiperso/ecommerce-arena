'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCart } from '@/lib/cart';

export default function Header() {
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();
  const { count } = useCart();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-8">
          <Link href="/" className="text-2xl font-bold text-black hover:text-gray-600 transition-colors">
            KICKS
          </Link>

          <form onSubmit={handleSearch} className="flex-1 max-w-sm hidden md:flex gap-2">
            <input
              type="text"
              placeholder="Search shoes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-white border border-gray-900 rounded-sm text-black placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-black transition-all"
            />
            <button type="submit" className="btn-primary">Search</button>
          </form>

          <div className="flex items-center gap-6">
            <Link href="/account" className="text-black hover:text-gray-600 transition-colors font-medium hidden md:block">
              Account
            </Link>
            <Link href="/cart" className="relative text-black hover:text-gray-600 transition-colors font-medium">
              Cart
              {count > 0 && (
                <span className="absolute -top-2 -right-4 bg-black text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {count}
                </span>
              )}
            </Link>
          </div>
        </div>

        <form onSubmit={handleSearch} className="md:hidden mt-4 flex gap-2">
          <input
            type="text"
            placeholder="Search shoes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2.5 bg-white border border-gray-900 rounded-sm text-black placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-black"
          />
          <button type="submit" className="btn-primary text-sm">Search</button>
        </form>
      </div>
    </header>
  );
}
