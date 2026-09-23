import { Locator, Page } from "@playwright/test";
import { BasePage } from "./base.page";

export class VeterinarianPage extends BasePage {
    readonly table: Locator;
    readonly nameRow: Locator;
    readonly specialtiesRow: Locator;
    readonly firstPageButton: Locator;
    readonly lastPageButton: Locator;

    constructor(page: Page) {
        super(page);
        this.table = this.page.getByRole('table');
        this.nameRow = this.table.getByRole('columnheader', { name: 'Name' });
        this.specialtiesRow = this.table.getByRole('columnheader', { name: 'Specialties' });
        this.firstPageButton = this.page.getByTitle('First');
        this.lastPageButton = this.page.getByTitle('Last');
    }

    async goto(): Promise<void> {
        await this.navigateTo('/vets.html');
        await this.waitForPageLoad();
    }
}