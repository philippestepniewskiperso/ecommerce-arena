import Link from 'next/link';
import { getProducts, getCategories } from '@/lib/api';

export const revalidate = 60;

export default async function Home() {
  const [products, categories] = await Promise.all([
    getProducts(0, 12),
    getCategories(),
  ]);

  return (
    <main className="min-h-screen bg-white">
      {/* Hero */}
      <div className="bg-black text-white py-32 border-b-8 border-gray-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-6xl sm:text-7xl font-bold mb-6 font-display tracking-tight">
            KICKS
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mb-10 font-light">
            Premium footwear collection. From streetwear to performance.
          </p>
          <div className="flex gap-4">
            <button className="px-8 py-3 bg-white text-black font-bold hover:bg-gray-200 transition-colors rounded-sm">
              Shop Now
            </button>
            <button className="px-8 py-3 bg-transparent border-2 border-white text-white hover:bg-white hover:text-black font-bold transition-all rounded-sm">
              Explore
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        {/* Categories */}
        {categories.length > 0 && (
          <section className="section mb-24">
            <h2 className="section-title">Collections</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/category/${cat.slug}`}
                  className="card p-8 text-center group hover:border-black transition-all"
                >
                  <div className="mb-4 text-5xl">👟</div>
                  <p className="font-bold text-lg text-black group-hover:underline transition-all">
                    {cat.name}
                  </p>
                  {cat.description && (
                    <p className="text-sm text-gray-600 mt-2">
                      {cat.description}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* New Arrivals */}
        <section className="section">
          <h2 className="section-title">New Arrivals</h2>
          {products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {products.map((product) => (
                <Link
                  key={product.id}
                  href={`/products/${product.slug}`}
                  className="product-card"
                >
                  <div className="product-image bg-gradient-to-br from-gray-100 to-gray-200">
                    <svg
                      className="w-20 h-20 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                  <div className="p-5">
                    <h3 className="font-bold text-base text-black mb-1 line-clamp-2">
                      {product.name}
                    </h3>
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                      {product.short_description}
                    </p>
                    <div className="flex items-end justify-between">
                      <p className="text-xl font-bold text-black">
                        €{product.base_price.toFixed(2)}
                      </p>
                      <span className="text-black transition-transform group-hover:translate-x-1">
                        →
                      </span>
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
