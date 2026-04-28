import Link from 'next/link';

interface Props {
  searchParams: { order?: string; total?: string };
}

export default function ConfirmationPage({ searchParams }: Props) {
  const orderNumber = searchParams.order ?? '—';
  const total = searchParams.total ? `€${parseFloat(searchParams.total).toFixed(2)}` : '';

  return (
    <main className="min-h-screen bg-white flex items-center justify-center">
      <div className="mx-auto max-w-lg px-4 text-center">
        <div className="text-6xl mb-6">✓</div>
        <h1 className="text-4xl font-bold text-black mb-3">Order Confirmed</h1>
        <p className="text-gray-600 mb-8">
          Thank you for your order. We'll send a confirmation email shortly.
        </p>

        <div className="bg-gray-50 rounded-sm p-6 mb-8 text-left">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm text-gray-600">Order number</span>
            <span className="font-bold text-black font-mono">{orderNumber}</span>
          </div>
          {total && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total charged</span>
              <span className="font-bold text-black">{total}</span>
            </div>
          )}
        </div>

        <div className="flex gap-4 justify-center">
          <Link href="/" className="btn-primary">
            Continue Shopping
          </Link>
        </div>
      </div>
    </main>
  );
}
