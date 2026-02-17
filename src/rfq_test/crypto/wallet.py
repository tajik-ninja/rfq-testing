"""Wallet management utilities."""

from dataclasses import dataclass
from typing import Optional

from eth_account import Account
from eth_account.hdaccount import generate_mnemonic, seed_from_mnemonic


@dataclass
class Wallet:
    """Wallet with private key and addresses."""
    
    private_key: str  # Hex without 0x prefix
    eth_address: str  # Ethereum address (for signing)
    inj_address: str  # Injective bech32 address
    
    @classmethod
    def from_private_key(cls, private_key: str) -> "Wallet":
        """Create wallet from private key.
        
        Args:
            private_key: Hex private key (with or without 0x prefix)
        """
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        
        account = Account.from_key(bytes.fromhex(private_key))
        eth_address = account.address
        
        # Convert Ethereum address to Injective bech32
        inj_address = eth_to_inj_address(eth_address)
        
        return cls(
            private_key=private_key,
            eth_address=eth_address,
            inj_address=inj_address,
        )
    
    @classmethod
    def generate(cls) -> "Wallet":
        """Generate a new random wallet."""
        account = Account.create()
        return cls.from_private_key(account.key.hex())


def eth_to_inj_address(eth_address: str) -> str:
    """Convert Ethereum address to Injective bech32 address.
    
    Args:
        eth_address: Ethereum address (0x...)
        
    Returns:
        Injective address (inj1...)
    """
    import bech32
    
    # Remove 0x prefix and convert to bytes
    if eth_address.startswith("0x"):
        eth_address = eth_address[2:]
    
    address_bytes = bytes.fromhex(eth_address)
    
    # Convert to bech32 with "inj" prefix
    converted = bech32.convertbits(address_bytes, 8, 5)
    if converted is None:
        raise ValueError(f"Failed to convert address: {eth_address}")
    
    return bech32.bech32_encode("inj", converted)


def inj_to_eth_address(inj_address: str) -> str:
    """Convert Injective bech32 address to Ethereum address.
    
    Args:
        inj_address: Injective address (inj1...)
        
    Returns:
        Ethereum address (0x...)
    """
    import bech32
    
    hrp, data = bech32.bech32_decode(inj_address)
    if hrp != "inj" or data is None:
        raise ValueError(f"Invalid Injective address: {inj_address}")
    
    converted = bech32.convertbits(data, 5, 8, False)
    if converted is None:
        raise ValueError(f"Failed to convert address: {inj_address}")
    
    return "0x" + bytes(converted).hex()


def generate_wallets_from_seed(
    seed_phrase: str,
    count: int,
    start_index: int = 0,
) -> list[Wallet]:
    """Generate multiple wallets from a seed phrase.
    
    Uses BIP-44 derivation path: m/44'/60'/0'/0/{index}
    
    Args:
        seed_phrase: 12 or 24 word mnemonic
        count: Number of wallets to generate
        start_index: Starting derivation index
        
    Returns:
        List of Wallet objects
    """
    Account.enable_unaudited_hdwallet_features()
    
    wallets = []
    for i in range(start_index, start_index + count):
        # Derive account at index
        account = Account.from_mnemonic(
            seed_phrase,
            account_path=f"m/44'/60'/0'/0/{i}",
        )
        wallets.append(Wallet.from_private_key(account.key.hex()))
    
    return wallets


def generate_mnemonic_phrase(num_words: int = 12) -> str:
    """Generate a new mnemonic phrase.
    
    Args:
        num_words: 12 or 24
        
    Returns:
        Space-separated mnemonic words
    """
    Account.enable_unaudited_hdwallet_features()
    
    if num_words == 12:
        return generate_mnemonic(num_words=12, lang="english")
    elif num_words == 24:
        return generate_mnemonic(num_words=24, lang="english")
    else:
        raise ValueError("num_words must be 12 or 24")
