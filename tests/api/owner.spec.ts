import { test, expect } from '../../fixtures/base.fixture';
import * as allure from 'allure-js-commons';

test.describe('Owner API', () => {
    test('should fetch owners from the API', async ({ request }) => {
        const response = await allure.step('Call owners API', async () => {
            return request.get('/owners/find');
        });

        await allure.step('Verify response status', async () => {
            expect(response.status()).toBe(200);
            expect(response.ok()).toBeTruthy();
        });
    });
});