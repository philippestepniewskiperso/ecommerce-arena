'use client';

import { useState } from 'react';
import { useCart } from '@/lib/cart';

interface Props {
  product_id: string;
  slug: string;
  name: string;
  sku_snapshot: string;
  unit_price: number;
}

export default function AddToCartButton({ product_id, slug, name, sku_snapshot, unit_price }: Props) {
  const { addItem } = useCart();
  const [added, setAdded] = useState(false);

  function handleAdd() {
    addItem({ product_id, slug, name, sku_snapshot, unit_price });
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  }

  return (
    <button
      onClick={handleAdd}
      className="w-full btn-primary py-4 text-base"
    >
      {added ? '✓ Added to cart' : 'Add to Cart'}
    </button>
  );
}
