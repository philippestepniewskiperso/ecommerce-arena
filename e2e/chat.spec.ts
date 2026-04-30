import { test, expect } from '@playwright/test';

const BACKOFFICE = 'http://localhost:3001';
const TS = Date.now();

// ── Widget unit tests ─────────────────────────────────────────────────────────

test.describe('Chat widget', () => {
  test('floating button visible on storefront', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: /open support chat/i })).toBeVisible();
  });

  test('unauthenticated click shows auth form', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /open support chat/i }).click();
    await expect(page.getByPlaceholder('Email')).toBeVisible();
    await expect(page.getByPlaceholder('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: /continue/i })).toBeVisible();
  });

  test('signup → ticket list → create ticket → chat view', async ({ page }) => {
    const email = `widget.${TS}@example.com`;

    await page.goto('/');
    await page.getByRole('button', { name: /open support chat/i }).click();

    // Sign up
    await page.getByPlaceholder('First name').fill('Widget');
    await page.getByPlaceholder('Last name').fill('Test');
    await page.getByPlaceholder('Email').fill(email);
    await page.getByPlaceholder('Password').fill('TestPassword1!');
    await page.getByRole('button', { name: /continue/i }).click();

    // Ticket list view
    await expect(page.getByText('New conversation')).toBeVisible();
    await expect(page.getByText('No previous conversations')).toBeVisible();

    // Create ticket
    await page.getByPlaceholder('Subject').fill(`Unit test ${TS}`);
    await page.getByPlaceholder(/describe/i).fill('Testing ticket creation');
    await page.getByRole('button', { name: /start conversation/i }).click();

    // Chat view, WS should connect
    await expect(page.getByText(`Unit test ${TS}`)).toBeVisible();
    await expect(page.getByText(/connected/i)).toBeVisible({ timeout: 5_000 });
  });

  test('second login shows previous conversations', async ({ page }) => {
    const email = `returning.${TS}@example.com`;
    const subject = `Previous ticket ${TS}`;

    // Create account and ticket
    await page.goto('/');
    await page.getByRole('button', { name: /open support chat/i }).click();
    await page.getByPlaceholder('First name').fill('Returning');
    await page.getByPlaceholder('Last name').fill('User');
    await page.getByPlaceholder('Email').fill(email);
    await page.getByPlaceholder('Password').fill('TestPassword1!');
    await page.getByRole('button', { name: /continue/i }).click();
    await expect(page.getByText('New conversation')).toBeVisible();
    await page.getByPlaceholder('Subject').fill(subject);
    await page.getByRole('button', { name: /start conversation/i }).click();
    await expect(page.getByText(subject)).toBeVisible({ timeout: 5_000 });

    // Go back to list
    await page.locator('button', { hasText: '←' }).click();
    await expect(page.getByText('Previous conversations')).toBeVisible();
    await expect(page.getByText(subject)).toBeVisible();
  });

  test('sign out button works', async ({ page }) => {
    const email = `signout.${TS}@example.com`;

    await page.goto('/');
    await page.getByRole('button', { name: /open support chat/i }).click();
    await page.getByPlaceholder('First name').fill('Sign');
    await page.getByPlaceholder('Last name').fill('Out');
    await page.getByPlaceholder('Email').fill(email);
    await page.getByPlaceholder('Password').fill('TestPassword1!');
    await page.getByRole('button', { name: /continue/i }).click();
    await expect(page.getByText('New conversation')).toBeVisible();

    await page.getByRole('button', { name: /sign out/i }).click();
    // Back to auth form
    await expect(page.getByPlaceholder('Email')).toBeVisible();
  });
});

// ── Live chat integration ─────────────────────────────────────────────────────

test.describe('Live chat exchange', () => {
  test('customer and staff exchange messages in real time', async ({ browser }) => {
    const customerCtx = await browser.newContext();
    const staffCtx = await browser.newContext();
    const customerPage = await customerCtx.newPage();
    const staffPage = await staffCtx.newPage();

    const email = `livechat.${TS}@example.com`;
    const subject = `Live chat ${TS}`;

    try {
      // ── Customer: signup + create ticket ────────────────────────────────────
      await customerPage.goto('http://localhost:3000');
      await customerPage.getByRole('button', { name: /open support chat/i }).click();
      await customerPage.getByPlaceholder('First name').fill('Live');
      await customerPage.getByPlaceholder('Last name').fill('Customer');
      await customerPage.getByPlaceholder('Email').fill(email);
      await customerPage.getByPlaceholder('Password').fill('TestPassword1!');
      await customerPage.getByRole('button', { name: /continue/i }).click();
      await expect(customerPage.getByText('New conversation')).toBeVisible();
      await customerPage.getByPlaceholder('Subject').fill(subject);
      await customerPage.getByRole('button', { name: /start conversation/i }).click();

      // Customer enters chat, WS connects
      await expect(customerPage.getByText(subject)).toBeVisible({ timeout: 5_000 });
      await expect(customerPage.getByText(/connected/i)).toBeVisible({ timeout: 5_000 });

      // Customer sends first message
      await customerPage.getByPlaceholder(/type a message/i).fill('Hello from customer');
      await customerPage.getByPlaceholder(/type a message/i).press('Enter');
      await expect(customerPage.getByText('Hello from customer')).toBeVisible();

      // ── Staff: login via API → inject token → navigate ──────────────────────
      const loginRes = await staffPage.request.post('http://localhost:3002/api/admin/auth/login', {
        data: { email: 'cs@demo.local', password: 'demo1234' },
      });
      const { token: staffToken } = await loginRes.json();
      await staffPage.goto(`${BACKOFFICE}`);
      await staffPage.evaluate((t) => localStorage.setItem('staff_token', t), staffToken);

      await staffPage.goto(`${BACKOFFICE}/support`);
      await expect(staffPage.getByText(subject)).toBeVisible({ timeout: 5_000 });
      await staffPage.getByText(subject).click();

      // Staff WS connects, sees customer message
      await expect(staffPage.getByText('● connected')).toBeVisible({ timeout: 5_000 });
      await expect(staffPage.getByText('Hello from customer')).toBeVisible();

      // Customer widget shows agent online
      await expect(customerPage.getByText(/agent online/i)).toBeVisible({ timeout: 5_000 });

      // ── Staff replies ────────────────────────────────────────────────────────
      await staffPage.getByPlaceholder(/reply to customer/i).fill('Hello from support');
      await staffPage.getByRole('button', { name: /send/i }).click();

      // Customer receives staff reply
      await expect(customerPage.getByText('Hello from support')).toBeVisible({ timeout: 5_000 });

      // ── Customer replies back ────────────────────────────────────────────────
      await customerPage.getByPlaceholder(/type a message/i).fill('Thanks!');
      await customerPage.getByPlaceholder(/type a message/i).press('Enter');

      // Staff receives customer reply
      await expect(staffPage.getByText('Thanks!')).toBeVisible({ timeout: 5_000 });

    } finally {
      await customerCtx.close();
      await staffCtx.close();
    }
  });
});
