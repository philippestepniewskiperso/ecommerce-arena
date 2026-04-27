const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3002';

export interface Product {
  id: string;
  name: string;
  slug: string;
  base_price: number;
  short_description?: string;
}

export interface ProductDetail extends Product {
  description?: string;
  category_id?: string;
  status: string;
  compare_price?: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  image_url?: string;
  parent_id?: string;
  position: number;
  created_at: string;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export async function getProducts(skip = 0, limit = 20): Promise<Product[]> {
  return fetchAPI(`/api/public/products?skip=${skip}&limit=${limit}`);
}

export async function searchProducts(q: string, skip = 0, limit = 20): Promise<Product[]> {
  return fetchAPI(`/api/public/products/search?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}`);
}

export async function getProduct(slug: string): Promise<ProductDetail> {
  return fetchAPI(`/api/public/products/${slug}`);
}

export async function getCategories(): Promise<Category[]> {
  return fetchAPI('/api/public/categories');
}

export async function getCategory(slug: string): Promise<Category> {
  return fetchAPI(`/api/public/categories/${slug}`);
}
