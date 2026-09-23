import { test as base } from '@playwright/test';
import { HomePage } from '../pages/home.page';
import { FindOwnersPage } from '../pages/findowners.page';
import { AddOwnersPage } from '../pages/addowners.page';
import { VeterinarianPage } from '../pages/veterinarian.page';

type CustomFixtures = {
    homepage: HomePage;
    findOwnersPage: FindOwnersPage;
    addOwnersPage: AddOwnersPage;
    veterinarianPage: VeterinarianPage;
};

export const test = base.extend<CustomFixtures>({

    homepage: async ({ page }, use) => {
        await use(new HomePage(page));
    },

    findOwnersPage: async ({ page }, use) => {
        await use(new FindOwnersPage(page));
    },

    addOwnersPage: async ({ page }, use) => {
        await use(new AddOwnersPage(page));
    },

    veterinarianPage: async ({ page }, use) => {
        await use(new VeterinarianPage(page));
    }
})

export { expect } from '@playwright/test';