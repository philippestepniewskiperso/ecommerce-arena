'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { searchProducts } from '@/lib/api';
import type { Product } from '@/lib/api';

export default function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const query = searchParams.q || '';
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(!!query);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!query) {
      setProducts([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');

    searchProducts(query)
      .then(setProducts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [query]);

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">
          ← Back
        </Link>

        <h1 className="text-4xl font-bold mb-2">Search</h1>

        <form className="mb-8" onSubmit={(e) => e.preventDefault()}>
          <input
            type="text"
            placeholder="Search products..."
            defaultValue={query}
            onChange={(e) => {
              const url = new URL(window.location.href);
              url.searchParams.set('q', e.target.value);
              window.history.pushState({}, '', url);
            }}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
          />
        </form>

        {error && <p className="text-red-600 mb-4">{error}</p>}
        {loading && <p className="text-gray-600">Searching...</p>}

        {!loading && query && products.length === 0 && (
          <p className="text-gray-600">No products found for &quot;{query}&quot;</p>
        )}

        {products.length > 0 && (
          <>
            <p className="text-gray-600 mb-6">Found {products.length} products</p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => (
                <Link
                  key={product.id}
                  href={`/products/${product.slug}`}
                  className="border rounded-lg overflow-hidden hover:shadow-lg transition"
                >
                  <div className="bg-gray-100 h-48 flex items-center justify-center">
                    <p className="text-gray-400">No image</p>
                  </div>
                  <div className="p-4">
                    <h3 className="font-bold text-lg mb-1">{product.name}</h3>
                    <p className="text-gray-600 text-sm mb-2 line-clamp-2">{product.short_description}</p>
                    <p className="text-xl font-bold">€{product.base_price.toFixed(2)}</p>
                  </div>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
