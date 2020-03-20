# Clover Orders Seeder

This script is intended to be used by developers to seed a Clover Sandbox account, assisting with your third-party application development and testing. It creates orders and makes in-full, credit card payments for those orders using the Clover REST APIs. These orders are based on the pre-existing inventory and customers of the merchant.

The order contains:
- 1 Random Customer
- 1 Random Line Item
- n Tax Rates in Line Items
- 1 or 2 Payments
- Randomly Included
    - 1 Line Items Modifier
    - 1 Discounts
    - 1 Tips

The credit card information in lines 17-20 is a test Visa provided by First Data. It will properly process fake payments in the Clover Sandbox environment, but is invalid for real transactions.

### Requirements

- Python 3.7.3 (backwards compatible with 2.7)
- pip
- [Clover Sandbox developer account](https://sandbox.dev.clover.com/developers)

### General Usage

- Open the file in a text editor and configure the script on lines 5-9.
- Ensure that your merchant has at least 1 inventory item.
- Ensure that your merchant has at least 1 modifier.
- Ensure that your merchant has at least 1 customer.
- Download the virtualenv packages with `pip install -r requirements.txt`
- Execute the script by running `python orders_seeder.py`

### Additional Information

The script `sleep`s in order to respect Clover's API rate limit. For more information, please reference our [Developer Guidelines](https://docs.clover.com/clover-platform/docs/api-usage-rate-limits).
The script consumes the following Clover API endpoints:  
- GET `v3/merchants/{MID}/items` to fetch a merchant's inventory
- GET `v3/merchants/{MID}/modifiers` to fetch a merchant's modifiers
- GET `v3/merchants/{MID}/customers` to fetch a merchant's customers
- POST `v3/merchants/{MID}/orders` to instantiate or update an open order  
- POST `v3/merchants/{MID}/orders/{orderID}/line_items` to add a line item to an order
- POST `v3/merchants/{MID}/orders/{orderID}/line_items/{itemID}/modifications` to add a modifier to a line item
- POST `v3/merchants/{MID}/orders/{orderID}/line_items/{itemID}/discounts` to add a discount to a line item
- POST `v3/merchants/{MID}/orders/{orderID}/discounts` to add a discount to an order
- [Developer Pay API](https://docs.clover.com/clover-platform/docs/developer-pay-api):
    - GET `v2/merchant/{MID}/pay/key` to fetch a merchant's developer pay secrets
    - POST `v2/merchant/{MID}/pay` to process the payment

For development and testing questions, please reference [our docs](https://docs.clover.com/), our [public developer forum](https://community.clover.com/).
