import { BasePage } from "./base.page";

export class HomePage extends BasePage {

    async goto(): Promise<void> {
        await this.navigateTo('/');
        await this.waitForPageLoad();
    }
}