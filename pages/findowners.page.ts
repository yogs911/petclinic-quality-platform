import { Locator, Page } from "@playwright/test";
import { BasePage } from "./base.page";

export class FindOwnersPage extends BasePage {
    readonly lastNameInput: Locator;
    readonly findOwnerButton: Locator;
    readonly addOwnerButton: Locator;
    readonly editOwnerButton: Locator;
    readonly addNewPetButton: Locator;
    readonly ownerInfoNameText: Locator;
    readonly ownerInfoAddressText: Locator;
    readonly ownerInfoCityText: Locator;
    readonly ownerInfoTelephoneText: Locator;

    constructor(page: Page) {
        super(page);
        this.lastNameInput = this.page.locator('#lastName');
        this.findOwnerButton = this.page.getByRole('button', { name: 'Find Owner' });
        this.addOwnerButton = this.page.getByRole('button', { name: 'Add Owner' });
        this.editOwnerButton = this.page.getByRole('button', { name: 'Edit Owner' });
        this.addNewPetButton = this.page.getByRole('button', { name: 'Add New Pet' });
        this.ownerInfoNameText = this.page.getByRole('row').filter({ hasText: 'Name' });
        this.ownerInfoAddressText = this.page.getByRole('row').filter({ hasText: 'Address' });
        this.ownerInfoCityText = this.page.getByRole('row').filter({ hasText: 'City' });
        this.ownerInfoTelephoneText = this.page.getByRole('row').filter({ hasText: 'Telephone' });
    }

     async goto(): Promise<void> {
        await this.navigateTo('/owners/find');
        await this.waitForPageLoad();
    }

    async goToAddOwnerPage(): Promise<void> {
        await this.addOwnerButton.click();
    }

    async findOwnerByLastName(lastName: string): Promise<void> {
        await this.lastNameInput.fill(lastName);
        await this.findOwnerButton.click();
    }
}