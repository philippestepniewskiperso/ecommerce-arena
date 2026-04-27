'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Header() {
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();

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
          <Link href="/" className="text-2xl font-bold text-black hover:text-gray-600 transition-colors font-display">
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
            <button
              type="submit"
              className="btn-primary"
            >
              Search
            </button>
          </form>

          <Link href="/account" className="text-black hover:text-gray-600 transition-colors font-medium">
            Account
          </Link>
        </div>

        <form onSubmit={handleSearch} className="md:hidden mt-4 flex gap-2">
          <input
            type="text"
            placeholder="Search shoes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2.5 bg-white border border-gray-900 rounded-sm text-black placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-black"
          />
          <button
            type="submit"
            className="btn-primary text-sm"
          >
            Search
          </button>
        </form>
      </div>
    </header>
  );
}
