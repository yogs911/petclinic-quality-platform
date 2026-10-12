import { test, expect } from '../../fixtures/base.fixture';

test('should display the error page', async ({ page }) => {
    const response = await page.goto('/error');

    expect(response).not.toBeNull();
    expect(response!.ok()).toBeFalsy();
    expect(response!.status()).toBe(500);
});
