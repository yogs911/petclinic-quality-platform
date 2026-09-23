import { Locator, Page } from '@playwright/test';

export class TopNavComponent {
    readonly page: Page;
    readonly homeLink: Locator;
    readonly findOwnersLink: Locator;
    readonly veterinariansLink: Locator;

    constructor(page: Page) {
        this.page = page;
        this.homeLink = this.page.getByRole('link', { name: ' Home' });
        this.findOwnersLink = this.page.getByRole('link', { name: ' Find Owners' });
        this.veterinariansLink = this.page.getByRole('link', { name: ' Veterinarians' });
    }

    async navigateTo(module: 'home' | 'findOwners' | 'veterinarians'): Promise<void> {
        const linkMap = {
            home: this.homeLink,
            findOwners: this.findOwnersLink,
            veterinarians: this.veterinariansLink,
        };
        await linkMap[module].click();
    }
}