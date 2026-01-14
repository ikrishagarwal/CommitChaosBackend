from web3 import Web3
from eth_account import Account
import time

ALCHEMY_URL = "https://eth-sepolia.g.alchemy.com/v2/oo4qeyqxmXeRomGEP9iNc"
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

if not w3.is_connected():
  raise Exception("❌ Web3 not connected")

print("✅ Connected to Sepolia | Chain ID:", w3.eth.chain_id)
CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0xfAe714242c0154ae2ACde4aD7cde90E438AAFd71"
)

ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_hash", "type": "bytes32"},
            {"internalType": "uint256", "name": "_expiry", "type": "uint256"}
        ],
        "name": "register",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"}
        ],
        "name": "isValid",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

SYSTEM_PRIVATE_KEY = "0x2b91b18d638169a58f8deb9922a3e423f44b408371f7d2229483dc8d1f8362bd"
account = Account.from_key(SYSTEM_PRIVATE_KEY)
SYSTEM_WALLET = account.address

print(" System wallet:", SYSTEM_WALLET)


def register_tourist(firebase_uid: str, expiry: int):
  """
  Registers tourist on blockchain and returns data for QR code
  """

  kyc_hash = Web3.keccak(text=firebase_uid)
  expiry_timestamp = expiry

  nonce = w3.eth.get_transaction_count(SYSTEM_WALLET, 'pending')

  tx = contract.functions.register(
      kyc_hash,
      expiry_timestamp
  ).build_transaction({
      "from": SYSTEM_WALLET,
      "nonce": nonce,
      "gas": 200000,
      "gasPrice": w3.eth.gas_price,
      "chainId": 11155111
  })

  signed_tx = w3.eth.account.sign_transaction(tx, SYSTEM_PRIVATE_KEY)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

  w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)

  return {
      "kyc_hash": kyc_hash.hex(),
      "expires_at": expiry_timestamp,
      "contract": CONTRACT_ADDRESS,
      "chain_id": 11155111
  }
