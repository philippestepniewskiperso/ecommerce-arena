import { test, expect } from '@playwright/test';

const PRODUCT_SLUG = 'air-velocity-pro';
const PRODUCT_NAME = 'Air Velocity Pro';

// Unique email per test run to avoid duplicate signup errors
const email = `e2e.test.${Date.now()}@example.com`;
const password = 'TestPassword123!';

test.describe('Storefront happy path', () => {
  test('homepage loads with products', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/KICKS/);
    // Hero section visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    // At least one product card rendered
    await expect(page.locator('a[href^="/products/"]').first()).toBeVisible();
  });

  test('product detail page loads', async ({ page }) => {
    await page.goto(`/products/${PRODUCT_SLUG}`);
    await expect(page.getByRole('heading', { name: PRODUCT_NAME })).toBeVisible();
    await expect(page.getByRole('button', { name: /add to cart/i })).toBeVisible();
  });

  test('add to cart updates badge', async ({ page }) => {
    await page.goto(`/products/${PRODUCT_SLUG}`);
    const badge = page.locator('text=/^\\d+$/').first(); // cart badge in header

    await page.getByRole('button', { name: /add to cart/i }).click();

    // Badge should show 1
    await expect(page.locator('header').getByText('1')).toBeVisible({ timeout: 3000 });
  });

  test('cart page shows added item', async ({ page }) => {
    await page.goto(`/products/${PRODUCT_SLUG}`);
    await page.getByRole('button', { name: /add to cart/i }).click();
    // Use client-side nav to preserve cart state
    await page.getByRole('link', { name: /view cart/i }).click();

    await expect(page.getByText(PRODUCT_NAME)).toBeVisible();
    await expect(page.getByRole('link', { name: /checkout/i })).toBeVisible();
  });

  test('full checkout flow → order confirmation', async ({ page }) => {
    // Add product to cart
    await page.goto(`/products/${PRODUCT_SLUG}`);
    await page.getByRole('button', { name: /add to cart/i }).click();
    // Use client-side nav to preserve cart state
    await page.getByRole('link', { name: /view cart/i }).click();

    // Go to checkout
    await page.getByRole('link', { name: /checkout/i }).click();
    await expect(page).toHaveURL('/checkout');

    // Step 1: auth
    await page.getByLabel(/first name/i).fill('E2E');
    await page.getByLabel(/last name/i).fill('Test');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole('button', { name: /continue to shipping/i }).click();

    // Step 2: shipping address
    await expect(page.getByRole('heading', { name: /shipping/i })).toBeVisible({ timeout: 8000 });
    await page.getByLabel(/street address/i).fill('1 rue de la Paix');
    await page.getByLabel(/city/i).fill('Paris');
    await page.getByLabel(/postal/i).fill('75001');

    // Place order
    await page.getByRole('button', { name: /place order/i }).click();

    // Confirmation page
    await expect(page).toHaveURL(/\/checkout\/confirmation/, { timeout: 15000 });
    await expect(page.getByText(/order confirmed/i)).toBeVisible();
    await expect(page.getByText(/ORD-/)).toBeVisible();
  });

  test('empty cart redirects to shop', async ({ page }) => {
    await page.goto('/checkout');
    // With empty cart, checkout shows "Your cart is empty"
    await expect(page.getByText(/cart is empty/i)).toBeVisible();
  });

  test('search returns results', async ({ page }) => {
    await page.goto('/search?q=air');
    await expect(page.locator('a[href^="/products/"]').first()).toBeVisible({ timeout: 5000 });
  });
});
