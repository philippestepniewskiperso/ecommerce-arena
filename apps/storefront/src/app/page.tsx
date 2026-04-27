import Link from 'next/link';
import { getProducts, getCategories } from '@/lib/api';

export const revalidate = 60; // ISR: revalidate every 60s

export default async function Home() {
  const [products, categories] = await Promise.all([
    getProducts(0, 12),
    getCategories(),
  ]);

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold mb-4">ecommerce-arena</h1>
        <p className="text-gray-600 mb-12">Production-grade e-commerce sandbox for agent testing</p>

        {/* Categories */}
        {categories.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-4">Categories</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {categories.map((cat) => (
                <Link key={cat.id} href={`/category/${cat.slug}`} className="p-4 border rounded hover:shadow-lg">
                  <p className="font-semibold">{cat.name}</p>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Products */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Featured Products</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <Link key={product.id} href={`/products/${product.slug}`} className="border rounded-lg overflow-hidden hover:shadow-lg transition">
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
        </div>
      </div>
    </main>
  );
}
