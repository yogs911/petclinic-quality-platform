import { test, expect } from '../../fixtures/base.fixture';
import * as allure from 'allure-js-commons';

test.describe('Veterinarian Page', () => {
    test('should display the veterinarian table with correct columns', async ({ veterinarianPage }) => {
       await allure.step('Navigate to Veterinarian page', async () => {
            await veterinarianPage.goto();
        });
        await allure.step('Verify table visibility', async () => {
            await expect(veterinarianPage.table).toBeVisible();
        });
        await allure.step('Verify column visibility', async () => {
            await expect(veterinarianPage.nameRow).toBeVisible();
            await expect(veterinarianPage.specialtiesRow).toBeVisible();
        });

        const tableText = await veterinarianPage.table.textContent();
        await allure.step('Click last page button', async () => {
            await veterinarianPage.lastPageButton.click();
        });

        const tableTextLast = await veterinarianPage.table.textContent();
        await allure.step('Verify table content change', async () => {
            expect(tableText).not.toEqual(tableTextLast);
        });

    });
});