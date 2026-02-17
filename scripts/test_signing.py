#!/usr/bin/env python3
"""Test that our Python signing matches the Go indexer's expectations.

This script creates a test signature and verifies we can recover the correct address.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eth_account import Account
from eth_hash.auto import keccak
import json

# Use a known test private key
TEST_PRIVATE_KEY = "YOURPRIVATEKEYHERE"
EXPECTED_ADDRESS = "YOURINJEXPECTEDADDRESSFROMPRIVATEKEYHERE"


def get_inj_address_from_private_key(private_key: str) -> str:
    """Convert private key to Injective bech32 address."""
    from pyinjective.wallet import PrivateKey
    
    if private_key.startswith("0x"):
        private_key = private_key[2:]
    
    priv_key = PrivateKey.from_hex(private_key)
    pub_key = priv_key.to_public_key()
    return pub_key.to_address().to_acc_bech32()


def test_address_derivation():
    """Test that we derive the correct address from private key."""
    address = get_inj_address_from_private_key(TEST_PRIVATE_KEY)
    print(f"Derived address: {address}")
    print(f"Expected address: {EXPECTED_ADDRESS}")
    assert address == EXPECTED_ADDRESS, f"Address mismatch: {address} != {EXPECTED_ADDRESS}"
    print("✓ Address derivation correct\n")


def test_signing_and_recovery():
    """Test that we can sign and recover the correct address."""
    # Build a test payload matching the Go test
    payload_dict = {
        "mi": "market_123",
        "id": 456,
        "t": "inj1taker",
        "td": "long",
        "tm": "100",
        "tq": "200",
        "m": EXPECTED_ADDRESS,  # Use the correct maker address
        "mq": "300",
        "mm": "400",
        "p": "500",
        "e": 1700000000000,
    }
    
    # JSON stringify (no spaces, preserve field order)
    payload_json = json.dumps(payload_dict, separators=(",", ":"))
    print(f"Payload JSON: {payload_json}")
    
    # Expected JSON from Go test
    expected_json = f'{{"mi":"market_123","id":456,"t":"inj1taker","td":"long","tm":"100","tq":"200","m":"{EXPECTED_ADDRESS}","mq":"300","mm":"400","p":"500","e":1700000000000}}'
    print(f"Expected JSON: {expected_json}")
    
    assert payload_json == expected_json, f"JSON mismatch:\nGot:      {payload_json}\nExpected: {expected_json}"
    print("✓ JSON serialization matches\n")
    
    # Hash with keccak256
    message_hash = keccak(payload_json.encode("utf-8"))
    print(f"Message hash: {message_hash.hex()}")
    
    # Sign with secp256k1
    account = Account.from_key(bytes.fromhex(TEST_PRIVATE_KEY))
    signature = account.unsafe_sign_hash(message_hash)
    
    # Serialize signature (r + s + v, 65 bytes)
    sig_bytes = (
        signature.r.to_bytes(32, "big") +
        signature.s.to_bytes(32, "big") +
        bytes([signature.v])
    )
    
    print(f"Signature (hex): 0x{sig_bytes.hex()}")
    print(f"Signature length: {len(sig_bytes)} bytes")
    print(f"v value: {signature.v}")
    
    # Recover the address from signature
    # Normalize v for recovery (Go expects 0/1, Python gives 27/28)
    v = signature.v
    if v >= 27:
        v -= 27
    
    recovery_sig = sig_bytes[:64] + bytes([v])
    
    from eth_account._utils.signing import to_standard_v
    recovered_address = Account._recover_hash(message_hash, signature=sig_bytes)
    print(f"Recovered ETH address: {recovered_address}")
    
    # Convert ETH address to Injective bech32
    from bech32 import bech32_encode, convertbits
    eth_bytes = bytes.fromhex(recovered_address[2:])  # Remove 0x prefix
    
    # Convert to 5-bit groups for bech32
    data = convertbits(eth_bytes, 8, 5)
    inj_address = bech32_encode("inj", data)
    print(f"Recovered INJ address: {inj_address}")
    
    assert inj_address == EXPECTED_ADDRESS, f"Recovered address mismatch: {inj_address} != {EXPECTED_ADDRESS}"
    print("✓ Signature recovery correct\n")


def test_full_signing_flow():
    """Test the full signing flow using our sign_quote function."""
    from rfq_test.crypto.signing import sign_quote, verify_signature
    
    # Sign a test quote
    signature = sign_quote(
        private_key=TEST_PRIVATE_KEY,
        rfq_id="456",
        market_id="market_123",
        direction="long",
        taker="inj1taker",
        taker_margin="100",
        taker_quantity="200",
        maker=EXPECTED_ADDRESS,
        maker_margin="400",
        maker_quantity="300",
        price="500",
        expiry=1700000000000,
    )
    
    print(f"Generated signature: 0x{signature}")
    print(f"Signature length: {len(bytes.fromhex(signature))} bytes")
    
    # Verify we can recover the correct address
    recovered = verify_signature(
        signature=signature,
        rfq_id="456",
        market_id="market_123",
        direction="long",
        taker="inj1taker",
        taker_margin="100",
        taker_quantity="200",
        maker=EXPECTED_ADDRESS,
        maker_margin="400",
        maker_quantity="300",
        price="500",
        expiry=1700000000000,
    )
    
    print(f"Recovered ETH address: {recovered}")
    
    # The recovered address should be the ETH address corresponding to our maker
    account = Account.from_key(bytes.fromhex(TEST_PRIVATE_KEY))
    expected_eth = account.address
    print(f"Expected ETH address: {expected_eth}")
    
    assert recovered.lower() == expected_eth.lower(), f"Recovery mismatch: {recovered} != {expected_eth}"
    print("✓ Full signing flow correct\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Python signing vs Go indexer expectations")
    print("=" * 60)
    print()
    
    test_address_derivation()
    test_signing_and_recovery()
    test_full_signing_flow()
    
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
