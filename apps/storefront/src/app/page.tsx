import Link from 'next/link';
import { getProducts, getCategories } from '@/lib/api';

export const revalidate = 60;

export default async function Home() {
  const [products, categories] = await Promise.all([
    getProducts(0, 12),
    getCategories(),
  ]);

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-5xl font-bold mb-4">ecommerce-arena</h1>
          <p className="text-xl text-blue-100">Production-grade e-commerce sandbox for agent testing</p>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        {/* Categories */}
        {categories.length > 0 && (
          <section className="section mb-16">
            <h2 className="section-title">Shop by Category</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/category/${cat.slug}`}
                  className="card p-6 text-center hover:border-blue-400 transition-colors"
                >
                  <p className="font-semibold text-lg text-gray-900">{cat.name}</p>
                  {cat.description && <p className="text-sm text-gray-600 mt-2">{cat.description}</p>}
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Products */}
        <section className="section">
          <h2 className="section-title">Featured Products</h2>
          {products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => (
                <Link
                  key={product.id}
                  href={`/products/${product.slug}`}
                  className="product-card group"
                >
                  <div className="product-image group-hover:from-gray-200 group-hover:to-gray-300 transition-colors relative overflow-hidden">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="font-bold text-lg text-gray-900 group-hover:text-blue-600 transition-colors mb-2 line-clamp-2">{product.name}</h3>
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2 h-10">{product.short_description}</p>
                    <div className="flex items-end justify-between">
                      <p className="text-2xl font-bold text-blue-600">€{product.base_price.toFixed(2)}</p>
                      <span className="text-blue-600 group-hover:translate-x-1 transition-transform">→</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="card p-12 text-center">
              <p className="text-gray-600">No products available</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
