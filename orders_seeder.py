#######################################
######### BEGIN SCRIPT CONFIG #########
#######################################

MID = ""
API_TOKEN = ""
NUM_ORDERS = 5
ENVIRONMENT = "https://sandbox.dev.clover.com/" # or https://api.clover.com/ or https://eu.clover.com/

#######################################
########## END SCRIPT CONFIG ##########
#######################################

######################################
########## OTHER CONSTANTS ###########
######################################
cardNumber = "6011361000006668"
expMonth = 12
expYear = 2020
CVV = None
######################################
######################################

import requests
import simplejson as json
from random import randint
import sys
from time import sleep
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64encode

headers = {"Authorization": "Bearer " + API_TOKEN}

# Fetch all items from a merchant
print("Fetching all items from merchant")
itemIds = []
url = ENVIRONMENT + "v3/merchants/" + MID + "/items?expand=taxRates"
response = requests.get(url, headers=headers)
if (response.status_code != 200):
    print("Something went wrong fetching this merchant's items")
    sys.exit()

items = json.loads(response.content)["elements"]

num_items = len(items)

if (num_items == 0):
    print("This merchant has no inventory. Create items and then re-run this script.")
    sys.exit()

for i in range(0, num_items):
    itemIds.append(str(items[i]["id"]))

# Fetch all customers from a merchant
print("Fetching all customers from merchant")
url = ENVIRONMENT + "v3/merchants/" + MID + "/customers?expand=emailAddresses%2CphoneNumbers%2Cmetadata"
response = requests.get(url, headers=headers)
if (response.status_code != 200):
    print("Something went wrong fetching this merchant's customers")
    sys.exit()

customers = json.loads(response.content)["elements"]

num_customers = len(customers)
if (num_customers == 0):
    print("This merchant has no customers. Create customers and then re-run this script.")
    sys.exit()

# Fetch all modifiers from a merchant
print("Fetching all modifiers from merchant")
url = ENVIRONMENT + "v3/merchants/" + MID + "/modifiers"
response = requests.get(url, headers=headers)
if (response.status_code != 200):
    print("Something went wrong fetching this merchant's modifiers")
    sys.exit()

modifiers = json.loads(response.content)["elements"]

num_modifiers = len(modifiers)
if (num_modifiers == 0):
    print("This merchant has no modifiers. Create modifiers and then re-run this script.")
    sys.exit()

# Fetch developer pay secrets from GET /v2/merchant/{mId}/pay/key
print("Fetching developer pay secret")
url = ENVIRONMENT + "v2/merchant/" + MID + "/pay/key"
response = requests.get(url, headers = headers)
if response.status_code != 200:
    print("Something went wrong fetching Developer Pay API secrets")
    sys.exit()
response = response.json()

modulus = int(response["modulus"])
exponent = int(response["exponent"])
prefix = str(response["prefix"])

RSAkey = RSA.construct((modulus, exponent))

# helper function
def print_progress(i):
    print((str((float(i + 1) / NUM_ORDERS) * 100)) + "% complete")

for i in range(0, NUM_ORDERS):
    print("###########################")
    sleep(0.1)
    print("Creating order")

    payload = { 
        "state": "open",
        }
    
    url = ENVIRONMENT + "v3/merchants/" + MID + "/orders?expand=customers"
    response = requests.post(url, headers=headers, json=payload)
    if (response.status_code != 200):
        print("Something went wrong creating an order")
        sys.exit()
    orderId = response.json()["id"]
    print("Order created: " + orderId)

    sleep(0.1)
    print("Adding customer")

    rand_customer_index = randint(0, num_customers - 1)
    url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId + "?expand=customers"
    payload = {
        "customers": {
            "elements": [
                customers[rand_customer_index],
            ]
        },
    }

    response = requests.post(url, headers=headers, json=payload)
    if (response.status_code != 200):
        print("Something went wrong adding the customer to the order")
        sys.exit()

    sleep(0.1)
    print("Adding item")

    url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId + "/line_items"

    rand_item_index = randint(0, num_items - 1)
    item = items[rand_item_index]
    
    taxRate = 0
    taxAmount = 0    
    taxRates = item["taxRates"]["elements"]
    for j in range(0, len(taxRates)):
        taxRate += int(taxRates[j]["rate"]) / 100000

    itemId = item["id"]
    payload = { 
        "item": { "id": itemId }
        }

    response = requests.post(url, headers=headers, json=payload)
    if (response.status_code != 200):
        print("Something went wrong adding a line item to the order")
        sys.exit()

    price = int(response.json()["price"])

    if(taxRate > 0):
        print("Adding tax rate")
        taxAmount = price / (100 / taxRate)
        price += taxAmount

    item = response.json()
    itemId = item["id"]
    
    if(randint(0, 1) == 1):
        sleep(0.1)
        print("Adding modifier to line item")

        url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId + "/line_items/" + itemId + "/modifications"
        rand_modifier_index = randint(0, num_modifiers - 1)
        modifier = modifiers[rand_modifier_index]
        payload = {
            "modifier": modifier
        }

        response = requests.post(url, headers=headers, json=payload)
        if (response.status_code != 200):
            print("Something went wrong adding a modifier to the line item")
            sys.exit()
        
        price += int(modifier["price"])
    
    addDiscount = randint(0, 2)
    shouldAddDiscount = False
    if(addDiscount == 1):
        # add discount to order
        print("Adding discount")
        shouldAddDiscount = True
        url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId + "/discounts"
    if(addDiscount == 2):
        # add discount to line item
        print("Adding discount to line item")
        shouldAddDiscount = True
        url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId + "/line_items/" + itemId + "/discounts"

    if(shouldAddDiscount):
        typeDiscount = randint(0, 1)
        discount = randint(1, 5)
        payload = {}
        if(typeDiscount == 0):
            # add amount discount
            print("Adding amount discount $" + str(discount))
            discount = discount * (-100)
            payload["name"] = "amount discount of"
            payload["amount"] = discount
        else:
            # add percentage discount
            print("Adding percentage discount " + str(discount) + "%")
            payload["name"] = "percentage discount of"
            payload["percentage"] = discount

        response = requests.post(url, headers=headers, json=payload)
        if (response.status_code != 200):
            print("Something went wrong adding a discount to the order")
            sys.exit()

        if(typeDiscount == 0):
            price += discount
        if(addDiscount == 1 and typeDiscount == 1):
            price = price - (price / (100 / discount))
        if(addDiscount == 2 and typeDiscount == 1):
            price = price - (int(item["price"]) / (100 / discount))

    tipAmount = 0
    if(randint(0, 1) == 1):
        print("Adding tip")
        tipAmount = ((price / 100) / (100 / randint(15, 30)) * 100)

    numPayments = randint(1, 2)
    amount = price / numPayments

    for j in range(0, numPayments):

        ########## BEGIN PAYMENT ##########
        # create a cipher from the RSA key and use it to encrypt the card number, prepended with the prefix from GET /v2/merchant/{mId}/pay/key
        cipher = PKCS1_OAEP.new(RSAkey)
        # encode str to byte (https://eli.thegreenplace.net/2012/01/30/the-bytesstr-dichotomy-in-python-3)
        encrypted = cipher.encrypt((prefix + cardNumber).encode())

        # Base64 encode the resulting encrypted data into a string to use as the cardEncrypted' property.
        cardEncrypted = b64encode(encrypted)

        if(j != 0):
            tipAmount = 0

        post_data = {
            "orderId": orderId,
            "currency": "usd",
            "amount": amount,
            "expMonth": expMonth,
            "cvv": CVV,
            "expYear": expYear,
            "cardEncrypted": cardEncrypted,
            "last4": cardNumber[-4:],
            "first6": cardNumber[0:6],
            "tipAmount": tipAmount,
            "taxAmount": taxAmount
        }
        
        sleep(0.1)
        print("'Paying' order")

        posturl = ENVIRONMENT + "v2/merchant/" + MID + "/pay"
        response = requests.post(
            posturl,
            headers = headers,
            data= post_data
            )
        if response.status_code != 200:
            print("Something went wrong during developer pay")
            sys.exit()
    
    url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId
    payload = {"total": price, "paymentState":"PAID"}
    
    sleep(0.1)
    response = requests.post(url=url, headers=headers, json=payload)
    if response.status_code != 200:
        print("Something went wrong updating order total")
        sys.exit()

    print_progress(i)