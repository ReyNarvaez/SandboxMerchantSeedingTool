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
url = ENVIRONMENT + "v3/merchants/" + MID + "/items"
response = requests.get(url, headers=headers)
if (response.status_code != 200):
    print("Something went wrong fetching this merchant's items")
    sys.exit()

elements = json.loads(response.content)["elements"]

for i in range(0, len(elements)):
    itemIds.append(str(elements[i]["id"]))

num_items = len(itemIds)
if (num_items == 0):
    print("This merchant has no inventory. Create items and then re-run this script.")
    sys.exit()

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
    
    sleep(0.1)
    print("Assigning customer to order")

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
        print("Something went wrong assigning the customer to the order")
        print(response)
        sys.exit()

    sleep(0.1)
    print("Assigning item to order")

    url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId + "/line_items"

    rand_item_index = randint(0, num_items - 1)
    payload = { 
        "item": { "id": itemIds[rand_item_index] },
        }

    response = requests.post(url, headers=headers, json=payload)
    if (response.status_code != 200):
        print("Something went wrong adding a line item to the order")
        sys.exit()

    price = int(response.json()["price"])
    tipAmount = 0
    if(randint(0, 1) == 1):
        tipAmount = ((price / 100) / (100 / randint(15, 30)) * 100)

    numPayments = randint(1, 2)

    for j in range(0, numPayments):

        ########## BEGIN PAYMENT ##########
        # create a cipher from the RSA key and use it to encrypt the card number, prepended with the prefix from GET /v2/merchant/{mId}/pay/key
        cipher = PKCS1_OAEP.new(RSAkey)
        # encode str to byte (https://eli.thegreenplace.net/2012/01/30/the-bytesstr-dichotomy-in-python-3)
        encrypted = cipher.encrypt((prefix + cardNumber).encode())

        # Base64 encode the resulting encrypted data into a string to use as the cardEncrypted' property.
        cardEncrypted = b64encode(encrypted)

        amount = price / numPayments

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
            "tipAmount": tipAmount
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


