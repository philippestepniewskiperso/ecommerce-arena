import Link from 'next/link';
import { getProduct, getProducts } from '@/lib/api';
import { notFound } from 'next/navigation';
import AddToCartButton from '@/components/AddToCartButton';

export const revalidate = 60;

interface Props {
  params: { slug: string };
}

export default async function ProductPage({ params }: Props) {
  let product;
  try {
    product = await getProduct(params.slug);
  } catch {
    notFound();
  }

  const relatedProducts = (await getProducts(0, 5)).filter(p => p.slug !== params.slug).slice(0, 4);

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <Link href="/" className="text-sm font-medium text-gray-600 hover:text-black transition-colors mb-8 inline-block">
          ← Back to shop
        </Link>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 mb-20">
          {/* Image */}
          <div className="bg-gray-100 aspect-square flex items-center justify-center rounded-sm">
            <svg className="w-24 h-24 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>

          {/* Info */}
          <div className="flex flex-col justify-center">
            <p className="text-sm text-gray-500 mb-2 uppercase tracking-widest">KICKS</p>
            <h1 className="text-4xl font-bold text-black mb-3">{product.name}</h1>
            <p className="text-gray-600 mb-6">{product.short_description}</p>

            <p className="text-3xl font-bold text-black mb-8">
              €{product.base_price.toFixed(2)}
            </p>

            <AddToCartButton
              product_id={product.id}
              slug={product.slug}
              name={product.name}
              sku_snapshot={product.slug.toUpperCase()}
              unit_price={product.base_price}
            />

            <Link
              href="/cart"
              className="w-full text-center btn-secondary py-4 text-base mt-3"
            >
              View Cart
            </Link>

            {product.description && (
              <div className="border-t border-gray-200 mt-8 pt-8">
                <h3 className="font-bold mb-3">About</h3>
                <p className="text-gray-600 leading-relaxed">{product.description}</p>
              </div>
            )}

            {product.tags && product.tags.length > 0 && (
              <div className="mt-6 flex flex-wrap gap-2">
                {product.tags.map((tag: string) => (
                  <span key={tag} className="bg-gray-100 px-3 py-1 rounded-sm text-sm text-gray-600">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {relatedProducts.length > 0 && (
          <div>
            <h2 className="section-title text-2xl mb-8">You might also like</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {relatedProducts.map((p) => (
                <Link key={p.id} href={`/products/${p.slug}`} className="product-card group">
                  <div className="product-image">
                    <svg className="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="p-4">
                    <p className="font-bold text-sm text-black group-hover:underline line-clamp-2">{p.name}</p>
                    <p className="text-black font-bold mt-1">€{p.base_price.toFixed(2)}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
