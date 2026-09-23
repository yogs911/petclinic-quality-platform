import { Locator, Page } from "@playwright/test";
import { BasePage } from "./base.page";

export class AddOwnersPage extends BasePage {
    readonly firstNameInput: Locator;
    readonly lastNameInput: Locator;
    readonly addressInput: Locator;
    readonly cityInput: Locator;
    readonly telephoneInput: Locator;
    readonly addOwnerButton: Locator;

    constructor(page: Page) {
        super(page);
        this.firstNameInput = this.page.locator('#firstName');
        this.lastNameInput = this.page.locator('#lastName');
        this.addressInput = this.page.locator('#address');
        this.cityInput = this.page.locator('#city');
        this.telephoneInput = this.page.locator('#telephone');
        this.addOwnerButton = this.page.locator('button:has-text("Add Owner")');
    }

    async goto(): Promise<void> {
        await this.navigateTo('/owners/new');
        await this.waitForPageLoad();
    }

    async addOwner(ownerData: any): Promise<void> {
        await this.firstNameInput.fill(ownerData.firstName);
        await this.lastNameInput.fill(ownerData.lastName);
        await this.addressInput.fill(ownerData.address);
        await this.cityInput.fill(ownerData.city);
        await this.telephoneInput.fill(ownerData.telephone);
        await this.addOwnerButton.click();
    }
}