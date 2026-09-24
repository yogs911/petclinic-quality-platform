import { test, expect } from '../../fixtures/base.fixture';
import * as allure from 'allure-js-commons';

test.describe('Home Page', () => {
    test('should have the correct title', async ({ homepage }) => {
       await allure.step('Navigate to Home page', async () => {
            await homepage.goto();
        });
        const title = await homepage.getTitle();
        await allure.step('Verify page title', () => {
            expect(title).toBe('PetClinic :: a Spring Framework demonstration');
        });
    });
})

