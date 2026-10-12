import { expect, Locator, Page } from "@playwright/test";
import { BasePage } from "./base.page";

export class AddPetPage extends BasePage {
    readonly nameInput: Locator;
    readonly birthDateInput: Locator;
    readonly typeSelect: Locator;
    readonly addPetButton: Locator;

    constructor(page: Page) {
        super(page);
        this.nameInput = this.page.locator('#name');
        this.birthDateInput = this.page.locator('#birthDate');
        this.typeSelect = this.page.locator('#type');
        this.addPetButton = this.page.getByRole('button', { name: 'Add Pet' });
    }

    petDetails(name: string): Locator {
        return this.page.locator('dl.dl-horizontal').filter({ hasText: name });
    }

    async goto(ownerId: number): Promise<void> {
        await this.navigateTo(`/owners/${ownerId}`);
        await this.waitForPageLoad();
        await this.page.getByRole('link', { name: 'Add New Pet' }).click();
        await this.waitForPageLoad();
    }

    async selectExistingOwner(): Promise<number> {
        await this.navigateTo('/owners');
        await this.waitForPageLoad();

        const ownerHref = await this.page.locator('a[href^="/owners/"]').evaluateAll((links) => {
            const ownerLink = links.find((link) => /^\/owners\/\d+$/.test(link.getAttribute('href') ?? ''));
            return ownerLink?.getAttribute('href');
        });

        expect(ownerHref, 'No existing owners were found in the application.').toBeTruthy();
        const ownerId = ownerHref?.match(/\/owners\/(\d+)/)?.[1];
        expect(ownerId, 'The selected owner URL did not contain a valid ID.').toBeTruthy();
        return Number(ownerId);
    }

    async addPet(petData: { name: string; birthDate: string; type: string }): Promise<void> {
        await this.nameInput.fill(petData.name);
        await this.birthDateInput.fill(petData.birthDate);
        await this.typeSelect.selectOption(petData.type);
        await this.addPetButton.click();
    }
}
