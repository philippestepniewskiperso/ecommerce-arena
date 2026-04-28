'use client';

import Link from 'next/link';
import { useCart } from '@/lib/cart';

export default function CartPage() {
  const { items, removeItem, updateQty, total, count } = useCart();

  const shipping = total < 100 ? 5.99 : 0;
  const tax = Math.round(total * 0.20 * 100) / 100;
  const grandTotal = Math.round((total + shipping + tax) * 100) / 100;

  if (items.length === 0) {
    return (
      <main className="min-h-screen bg-white">
        <div className="mx-auto max-w-2xl px-4 py-20 text-center">
          <h1 className="text-4xl font-bold text-black mb-4">Your cart is empty</h1>
          <p className="text-gray-600 mb-8">Add some shoes to get started.</p>
          <Link href="/" className="btn-primary">Continue Shopping</Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold text-black mb-10">Your Cart ({count})</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Items */}
          <div className="lg:col-span-2 space-y-6">
            {items.map((item) => (
              <div key={item.product_id} className="flex gap-6 border-b border-gray-200 pb-6">
                <div className="w-24 h-24 bg-gray-100 flex items-center justify-center rounded-sm flex-shrink-0">
                  <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold text-black">{item.name}</h3>
                      <p className="text-sm text-gray-500">{item.sku_snapshot}</p>
                    </div>
                    <p className="font-bold text-black">€{(item.unit_price * item.quantity).toFixed(2)}</p>
                  </div>
                  <div className="flex items-center gap-4 mt-3">
                    <div className="flex items-center border border-gray-900 rounded-sm">
                      <button
                        onClick={() => updateQty(item.product_id, item.quantity - 1)}
                        className="px-3 py-1 text-black hover:bg-gray-100 transition-colors"
                      >
                        −
                      </button>
                      <span className="px-3 py-1 text-black font-medium">{item.quantity}</span>
                      <button
                        onClick={() => updateQty(item.product_id, item.quantity + 1)}
                        className="px-3 py-1 text-black hover:bg-gray-100 transition-colors"
                      >
                        +
                      </button>
                    </div>
                    <button
                      onClick={() => removeItem(item.product_id)}
                      className="text-sm text-gray-500 hover:text-black transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="bg-gray-50 p-6 rounded-sm h-fit">
            <h2 className="text-xl font-bold text-black mb-6">Order Summary</h2>
            <div className="space-y-3 text-sm mb-6">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-medium">€{total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span className="font-medium">{shipping === 0 ? 'Free' : `€${shipping.toFixed(2)}`}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax (20%)</span>
                <span className="font-medium">€{tax.toFixed(2)}</span>
              </div>
              {shipping === 0 && (
                <p className="text-xs text-green-700 font-medium">✓ Free shipping applied</p>
              )}
            </div>
            <div className="border-t border-gray-300 pt-4 flex justify-between mb-6">
              <span className="font-bold text-black">Total</span>
              <span className="font-bold text-black text-xl">€{grandTotal.toFixed(2)}</span>
            </div>
            <Link href="/checkout" className="block w-full btn-primary text-center py-4">
              Checkout
            </Link>
            <Link href="/" className="block text-center mt-3 text-sm text-gray-600 hover:text-black transition-colors">
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
