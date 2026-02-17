"""Derive private key from mnemonic. Usage: python3 derive_key.py word1 word2 word3 ..."""
import sys
from eth_account import Account
import bech32

Account.enable_unaudited_hdwallet_features()

if len(sys.argv) < 2:
    print("Usage: python3 derive_key.py your mnemonic words here")
    sys.exit(1)

mnemonic = " ".join(sys.argv[1:])
acct = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")

eth_addr = acct.address
addr_bytes = bytes.fromhex(eth_addr[2:])
inj_addr = bech32.bech32_encode("inj", bech32.convertbits(addr_bytes, 8, 5))

print(f"Private Key: {acct.key.hex()}")
print(f"ETH Address: {eth_addr}")
print(f"INJ Address: {inj_addr}")
