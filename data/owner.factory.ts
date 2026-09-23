import {faker} from '@faker-js/faker';

export class OwnerFactory {
    static generateOwnerData() {
        return {
            firstName: faker.person.firstName(),
            lastName: faker.person.lastName(),
            address: faker.location.streetAddress(),
            city: faker.location.city(),
            telephone: faker.phone.number({'style': 'mobile'}) // Generates a 10-digit number
        };
    }
}