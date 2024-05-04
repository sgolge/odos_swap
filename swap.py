import json
import sys
import requests
from web3 import Web3


token_price_base_url = f"https://api.odos.xyz/pricing/token"
user_address='0x0002e2055B5ccBcb3AAdB4bc8500Bdf0f970774A'
user_address_PK=''

chain_id = 8453 # the chain id the token/asset is from
num = 1 * (10 ** 18)

def get_price(chain_id=chain_id, token_address = "",currency_id = "USD"):
    response = requests.get(f"{token_price_base_url}/{chain_id}/{token_address}") #,params={"currencyId": currency_id}
    token_price=0.0
    if response.status_code == 200:
      token_price = response.json()
      token_price=token_price['price']
      print(token_price)

    else:
      print(f"Error getting token price: {response.json()}")

    return token_price

def post_quote(chain_id=chain_id, token_IN_address = '',token_OUT_address='',amount='1',currency_id = "USD"):
    quote_url = "https://api.odos.xyz/sor/quote/v2"

    amount = num * float(amount)
    amount = "{:.0f}".format(round(amount, 0))
    quote=None

    quote_request_body = {
        "chainId": chain_id,  # Replace with desired chainId
        "inputTokens": [
            {
                "tokenAddress": token_IN_address,  # checksummed input token address
                "amount": str(amount),  # input amount as a string in fixed integer precision
            }
        ],
        "outputTokens": [
            {
                "tokenAddress": token_OUT_address,  # checksummed output token address
                "proportion": 1
            }
        ],
        "slippageLimitPercent": 0.8,  # set your slippage limit percentage (1 = 1%)
        "userAddr": user_address,  # checksummed user address
        "referralCode": 0,  # referral code (recommended)
        "disableRFQs": True,
        "compact": True,
    }

    response = requests.post(
        quote_url,params={"currencyId": currency_id},
        headers={"Content-Type": "application/json"},
        json=quote_request_body
    )

    if response.status_code == 200:
        quote = response.json()
        # handle quote response data
    else:
        print(f"Error in Quote: {response.json()}")
        # handle quote failure cases
    return quote


def assemble_quote(chain_id=chain_id,pathId='', userAddr = user_address,currency_id = "USD"):
    assemble_url = "https://api.odos.xyz/sor/assemble"

    assemble_request_body = {
        "userAddr": user_address,  # the checksummed address used to generate the quote
        "pathId": pathId,  # Replace with the pathId from quote response in step 1
        "simulate": True,
        # this can be set to true if the user isn't doing their own estimate gas call for the transaction
    }

    response = requests.post(
        assemble_url,
        headers={"Content-Type": "application/json"},
        json=assemble_request_body
    )

    if response.status_code == 200:
        assembled_transaction = response.json()
        # handle Transaction Assembly response data
    else:
        print(f"Error in Transaction Assembly: {response.json()}")
        # handle Transaction Assembly failure cases
    return assembled_transaction


def execute_transaction(assembled_transaction='',):
    # 1. create web3 provider
    w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
    # 2. Extract transaction object from assemble API response
    transaction = assembled_transaction["transaction"]
    # 3. Sign tx with a private key
    pk = str(user_address_PK)
    # web3py requires the value to be an integer
    transaction["value"] = int(transaction["value"])
    signed_tx = w3.eth.account.sign_transaction(transaction, pk)
    # 4. Send the signed transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return tx_hash

USDC_Base='0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
DAI_Base='0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb'
WETH_Base = "0x4200000000000000000000000000000000000006"

token_price=get_price(token_address=USDC_Base)
token_price=get_price(token_address=DAI_Base)
token_price=get_price(token_address=WETH_Base)
results_quote=post_quote(token_IN_address=DAI_Base, token_OUT_address=USDC_Base,amount=1)
pathId=results_quote['pathId']
assembled_transaction=assemble_quote(pathId=pathId)
tx_hash=execute_transaction(assembled_transaction=assembled_transaction)
print(tx_hash)
