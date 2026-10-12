import { test, expect } from '../../fixtures/base.fixture';
import * as allure from 'allure-js-commons';

const petData = {
    name: `PlaywrightPet-${Date.now()}`,
    birthDate: '2024-01-15',
    type: 'dog',
};

test.describe('Owner Pet Page', () => {
    test('should add a new pet for an existing owner', async ({ addPetPage }) => {
        const ownerId = await allure.step('Find an existing owner', async () => {
            return addPetPage.selectExistingOwner();
        });

        await allure.step('Navigate to the selected owner', async () => {
            await addPetPage.goto(ownerId);
        });

        await allure.step('Add a pet to the owner', async () => {
            await addPetPage.addPet(petData);
        });

        await allure.step('Verify the created pet appears on the owner', async () => {
            const petDetails = addPetPage.petDetails(petData.name);
            await expect(petDetails).toContainText(petData.name);
            await expect(petDetails).toContainText('2024-01-15');
            await expect(petDetails).toContainText('dog');
        });
    });
});
