#######################################
######### BEGIN SCRIPT CONFIG #########
#######################################

MID = ""
API_TOKEN = ""
NUM_ORDERS = 50
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

# Fetch all items from a merchant
print("Fetching all items from merchant")
itemIds = []
url = ENVIRONMENT + "v3/merchants/" + MID + "/items"
headers = {"Authorization": "Bearer " + API_TOKEN}
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
headers = {"Authorization": "Bearer " + API_TOKEN}
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
headers = {"Authorization": "Bearer " + API_TOKEN}
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

    price = response.json()["price"]

    ########## BEGIN PAYMENT ##########
    # create a cipher from the RSA key and use it to encrypt the card number, prepended with the prefix from GET /v2/merchant/{mId}/pay/key
    cipher = PKCS1_OAEP.new(RSAkey)
    # encode str to byte (https://eli.thegreenplace.net/2012/01/30/the-bytesstr-dichotomy-in-python-3)
    encrypted = cipher.encrypt((prefix + cardNumber).encode())

    # Base64 encode the resulting encrypted data into a string to use as the cardEncrypted' property.
    cardEncrypted = b64encode(encrypted)

    post_data = {
        "orderId": orderId,
        "currency": "usd",
        "amount": int(price),
        "expMonth": expMonth,
        "cvv": CVV,
        "expYear": expYear,
        "cardEncrypted": cardEncrypted,
        "last4": cardNumber[-4:],
        "first6": cardNumber[0:6]
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
    payload = {"total": int(price)}
    sleep(0.1)
    response = requests.post(url=url, headers=headers, json=payload)
    if response.status_code != 200:
        print("Something went wrong updating order total")
        sys.exit()

    print_progress(i)

# orderIds = ["H7A14PDB9QJWW","2M52VJ5P7Q4VP","VE5RYXC5V54Y6","7DSNC6XGQ7Y86","JE18B7EHBQJ8W","CERDA1ATCXRCJ","HKEBD6SBYS9F8","86F0P1AX4TAQ2","GD1TENN469AW0","0VXMDC24F01M4","97WA62M2DG67T","9Z3TS0WNW70KT","KSJ94XRS41S80","N8HB8WN3XHZTC","5XAFGYG1H2KET","K9WXFEMX4VESE","NFAK5BHAA8RF4","QQ4MQE6XMK4QG","PDF80BCPVKE0Y","Z9MYKXYQW7GB6","JSWC44TWNCYBT","WP2PZ6YAY3ZQE","HE7NDTDCCJ4MY","BYH5T3P1FV0JE","TQ8Q76X3KWV4J","3DSBR599R3DWA","C2JMDX1Y079HE","EP4JDYENBR6GJ","9ZAM0F6VHFRB8","E7VGAKD7H70ZW","GN8FN224SDH5T","KXDVGWHN48J9C","YMHZQQ5HMKR50","5T1WQW8Q9Z4Y2","4RZQDSF4DN65T","ECH9M5H38H2M0","253BYZCS8BCJ6","3F53TX8AJT8CC","ZFKF33X40Y4DJ","ZMZF5Y71GJDQT","NWG8K6KZB53FG","JKQAMWEJNMWQP","8SZSAMPV9PF2Y","QNX8JQC7SXSH0","3WYKKSSH7FRS8","K3NR9CW517ZNT","9CTH6Q5F90J9Y","M8W0JPJZ3AHGC","6HPTDQ2D96M50","0KV41KC3Q4X40","FQJA0WQ9KAD7C","RNGV8XBFW5JSY"]
# url = "https://sandbox.dev.clover.com/v3/merchants/merchantid/orders/orderid"

# for i in range(0, len(orderIds)):
#     url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderIds[i]
#     headers = {"Authorization": "Bearer " + API_TOKEN}
#     response = requests.delete(url, headers = headers)
#     if (response.status_code != 200):
#         print("Something went wrong deleting an order")
#         sys.exit()

# print(json.loads(json.dumps(customers[1])))

# orderIds = ["V87CPS5M31JR8","NJW8412WBMXEY","H7A14PDB9QJWW","2M52VJ5P7Q4VP","VE5RYXC5V54Y6","7DSNC6XGQ7Y86","JE18B7EHBQJ8W","CERDA1ATCXRCJ","HKEBD6SBYS9F8","86F0P1AX4TAQ2","GD1TENN469AW0","0VXMDC24F01M4","97WA62M2DG67T","9Z3TS0WNW70KT","KSJ94XRS41S80","N8HB8WN3XHZTC","5XAFGYG1H2KET","K9WXFEMX4VESE","NFAK5BHAA8RF4","QQ4MQE6XMK4QG","PDF80BCPVKE0Y","Z9MYKXYQW7GB6","JSWC44TWNCYBT","WP2PZ6YAY3ZQE","HE7NDTDCCJ4MY","BYH5T3P1FV0JE","TQ8Q76X3KWV4J","3DSBR599R3DWA","C2JMDX1Y079HE","EP4JDYENBR6GJ","9ZAM0F6VHFRB8","E7VGAKD7H70ZW","GN8FN224SDH5T","KXDVGWHN48J9C","YMHZQQ5HMKR50","5T1WQW8Q9Z4Y2","4RZQDSF4DN65T","ECH9M5H38H2M0","253BYZCS8BCJ6","3F53TX8AJT8CC","ZFKF33X40Y4DJ","ZMZF5Y71GJDQT","NWG8K6KZB53FG","JKQAMWEJNMWQP","8SZSAMPV9PF2Y","QNX8JQC7SXSH0","3WYKKSSH7FRS8","K3NR9CW517ZNT","9CTH6Q5F90J9Y","M8W0JPJZ3AHGC","6HPTDQ2D96M50","0KV41KC3Q4X40","FQJA0WQ9KAD7C","RNGV8XBFW5JSY"]
# for i in range (0, len(orderIds)):
#     sleep(0.1)
#     rand_customer_index = randint(0, num_customers - 1)
#     orderId = orderIds[i]
#     url = ENVIRONMENT + "v3/merchants/" + MID + "/orders/" + orderId
#     print("Appending customer to order " + url)
#     payload = {
#         "customers": {
#             "elements": [
#                 customers[rand_customer_index],
#             ]
#         },
#     }

#     response = requests.post(url, headers=headers, json=payload)
#     if (response.status_code != 200):
#         print("Something went wrong adding a cutomer to the order")
#         print(response)
#         sys.exit()

# ADD EXPAND CUSOTMERS TO ORDERS REQUESTS (https://community.clover.com/questions/840/add-a-customer-to-an-order-through-the-rest-api.html)
