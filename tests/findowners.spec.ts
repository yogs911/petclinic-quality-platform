import { OwnerFactory } from '../data/owner.factory';
import { test, expect } from '../fixtures/base.fixture';
import * as allure from 'allure-js-commons';

test.describe('Find Owners Page', () => {

    test('should add new owner', async ({ addOwnersPage , findOwnersPage}) => {
        await allure.step('Navigate to Add Owner page', async () => {
            await addOwnersPage.goto();
        });
        const ownerData = OwnerFactory.generateOwnerData();
        await allure.step('Add new owner', async () => {
            await addOwnersPage.addOwner(ownerData);
        });
        await allure.step('Verify owner information', async () => {
            await expect(findOwnersPage.ownerInfoNameText).toContainText(ownerData.firstName + ' ' + ownerData.lastName);
            await expect(findOwnersPage.ownerInfoCityText).toContainText(ownerData.city);
            await expect(findOwnersPage.ownerInfoTelephoneText).toContainText(ownerData.telephone);
        });
    });
});
