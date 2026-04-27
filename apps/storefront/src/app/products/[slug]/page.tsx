import Link from 'next/link';
import { getProduct, getProducts } from '@/lib/api';
import { notFound } from 'next/navigation';

export const revalidate = 60; // ISR

interface Props {
  params: {
    slug: string;
  };
}

export default async function ProductPage({ params }: Props) {
  let product;
  try {
    product = await getProduct(params.slug);
  } catch {
    notFound();
  }

  const relatedProducts = await getProducts(0, 4);

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">
          ← Back
        </Link>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Image */}
          <div className="bg-gray-100 rounded-lg h-96 flex items-center justify-center">
            <p className="text-gray-400">No image</p>
          </div>

          {/* Info */}
          <div>
            <h1 className="text-4xl font-bold mb-2">{product.name}</h1>
            <p className="text-gray-600 mb-4">{product.short_description}</p>

            <div className="flex items-baseline gap-2 mb-6">
              <p className="text-3xl font-bold">€{product.base_price.toFixed(2)}</p>
              {product.compare_price && (
                <p className="text-lg text-gray-400 line-through">€{product.compare_price.toFixed(2)}</p>
              )}
            </div>

            <button className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 mb-4">
              Add to Cart
            </button>

            <div className="border-t pt-4">
              <h3 className="font-semibold mb-2">About this product</h3>
              <p className="text-gray-600">{product.description}</p>
            </div>

            {product.tags.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-semibold mb-2">Tags:</p>
                <div className="flex flex-wrap gap-2">
                  {product.tags.map((tag) => (
                    <span key={tag} className="bg-gray-200 px-2 py-1 rounded text-sm">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Related Products */}
        {relatedProducts.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-4">Related Products</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {relatedProducts.map((p) => (
                <Link key={p.id} href={`/products/${p.slug}`} className="border rounded hover:shadow-lg">
                  <div className="bg-gray-100 h-32 flex items-center justify-center">
                    <p className="text-gray-400 text-sm">No image</p>
                  </div>
                  <div className="p-3">
                    <p className="font-semibold text-sm line-clamp-2">{p.name}</p>
                    <p className="text-lg font-bold">€{p.base_price.toFixed(2)}</p>
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
