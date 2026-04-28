'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useCart } from '@/lib/cart';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3002';

export default function CheckoutPage() {
  const { items, total, clearCart } = useCart();
  const router = useRouter();

  const [form, setForm] = useState({
    email: '', password: '',
    first_name: '', last_name: '',
    line1: '', city: '', postal_code: '', country_code: 'FR',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'auth' | 'shipping'>('auth');
  const [token, setToken] = useState('');

  const shipping = total < 100 ? 5.99 : 0;
  const tax = Math.round(total * 0.20 * 100) / 100;
  const grandTotal = Math.round((total + shipping + tax) * 100) / 100;

  if (items.length === 0) {
    return (
      <main className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Your cart is empty.</p>
          <Link href="/" className="btn-primary">Shop Now</Link>
        </div>
      </main>
    );
  }

  async function handleAuth(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Try login first
      let res = await fetch(`${API}/api/customer/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email, password: form.password }),
      });

      if (res.status === 401) {
        // Try signup
        res = await fetch(`${API}/api/customer/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: form.email,
            password: form.password,
            first_name: form.first_name || 'Guest',
            last_name: form.last_name || 'User',
          }),
        });
      }

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Authentication failed');
      }

      const data = await res.json();
      setToken(data.token);
      setStep('shipping');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  }

  async function handlePlaceOrder(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        items: items.map(i => ({
          product_id: i.product_id,
          name_snapshot: i.name,
          sku_snapshot: i.sku_snapshot,
          unit_price: i.unit_price,
          quantity: i.quantity,
        })),
        shipping_address: {
          first_name: form.first_name || 'Guest',
          last_name: form.last_name || 'User',
          line1: form.line1,
          city: form.city,
          postal_code: form.postal_code,
          country_code: form.country_code,
        },
        card_token: 'tok_test',
      };

      const res = await fetch(`${API}/api/customer/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Order failed');
      }

      if (data.payment_status === 'failed') {
        throw new Error(data.error || 'Payment declined');
      }

      clearCart();
      router.push(`/checkout/confirmation?order=${data.order_number}&total=${data.total}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Checkout failed');
    } finally {
      setLoading(false);
    }
  }

  const update = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }));

  return (
    <main className="min-h-screen bg-white">
      <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
        <h1 className="text-4xl font-bold text-black mb-10">Checkout</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Form */}
          <div className="lg:col-span-2">
            {step === 'auth' ? (
              <form onSubmit={handleAuth} className="space-y-4">
                <h2 className="text-xl font-bold text-black mb-4">Your account</h2>
                <p className="text-sm text-gray-600 mb-6">Log in or we'll create an account for you.</p>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-black mb-1">First name</label>
                    <input id="first_name" value={form.first_name} onChange={update('first_name')} placeholder="Jean"
                      className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black" />
                  </div>
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-black mb-1">Last name</label>
                    <input id="last_name" value={form.last_name} onChange={update('last_name')} placeholder="Dupont"
                      className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black" />
                  </div>
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-black mb-1">Email *</label>
                  <input id="email" type="email" required value={form.email} onChange={update('email')} placeholder="jean@example.com"
                    className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black" />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-black mb-1">Password *</label>
                  <input id="password" type="password" required value={form.password} onChange={update('password')} placeholder="••••••••"
                    className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black" />
                </div>

                {error && <p className="text-red-600 text-sm">{error}</p>}

                <button type="submit" disabled={loading} className="btn-primary w-full py-4 disabled:opacity-50">
                  {loading ? 'Please wait...' : 'Continue to Shipping'}
                </button>
              </form>
            ) : (
              <form onSubmit={handlePlaceOrder} className="space-y-4">
                <h2 className="text-xl font-bold text-black mb-4">Shipping address</h2>

                <div>
                  <label htmlFor="line1" className="block text-sm font-medium text-black mb-1">Street address *</label>
                  <input id="line1" required value={form.line1} onChange={update('line1')} placeholder="123 rue de la Paix"
                    className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="city" className="block text-sm font-medium text-black mb-1">City *</label>
                    <input id="city" required value={form.city} onChange={update('city')} placeholder="Paris"
                      className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black" />
                  </div>
                  <div>
                    <label htmlFor="postal_code" className="block text-sm font-medium text-black mb-1">Postal code *</label>
                    <input id="postal_code" required value={form.postal_code} onChange={update('postal_code')} placeholder="75001"
                      className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-black mb-1">Country</label>
                  <select value={form.country_code} onChange={update('country_code')}
                    className="w-full border border-gray-900 rounded-sm px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-black bg-white">
                    <option value="FR">France</option>
                    <option value="DE">Germany</option>
                    <option value="ES">Spain</option>
                    <option value="IT">Italy</option>
                    <option value="GB">United Kingdom</option>
                    <option value="US">United States</option>
                  </select>
                </div>

                <div className="border-t border-gray-200 pt-6 mt-6">
                  <h2 className="text-xl font-bold text-black mb-4">Payment</h2>
                  <div className="border border-gray-900 rounded-sm px-4 py-3 bg-gray-50">
                    <p className="text-sm text-gray-700 font-medium">💳 Test card (mock processor)</p>
                    <p className="text-xs text-gray-500 mt-1">No real payment — sandbox environment</p>
                  </div>
                </div>

                {error && <p className="text-red-600 text-sm">{error}</p>}

                <button type="submit" disabled={loading} className="btn-primary w-full py-4 disabled:opacity-50">
                  {loading ? 'Placing order...' : `Place Order · €${grandTotal.toFixed(2)}`}
                </button>

                <button type="button" onClick={() => setStep('auth')} className="text-sm text-gray-600 hover:text-black w-full text-center mt-2">
                  ← Back
                </button>
              </form>
            )}
          </div>

          {/* Order summary */}
          <div className="bg-gray-50 p-6 rounded-sm h-fit">
            <h2 className="text-lg font-bold text-black mb-4">Order Summary</h2>
            <div className="space-y-3 mb-6">
              {items.map(item => (
                <div key={item.product_id} className="flex justify-between text-sm">
                  <span className="text-gray-700">{item.name} <span className="text-gray-500">×{item.quantity}</span></span>
                  <span className="font-medium">€{(item.unit_price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="border-t border-gray-200 pt-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span>€{total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span>{shipping === 0 ? 'Free' : `€${shipping.toFixed(2)}`}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax (20%)</span>
                <span>€{tax.toFixed(2)}</span>
              </div>
            </div>
            <div className="border-t border-gray-300 mt-4 pt-4 flex justify-between">
              <span className="font-bold text-black">Total</span>
              <span className="font-bold text-black text-lg">€{grandTotal.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
