"""Admin actor for contract administration."""

import logging
from typing import Optional

from rfq_test.clients.contract import ContractClient
from rfq_test.crypto.wallet import Wallet
from rfq_test.models.config import ContractConfig, ChainConfig

logger = logging.getLogger(__name__)


class Admin:
    """Admin actor for managing market makers.
    
    The admin is the contract owner who can:
    - Register market makers
    - Revoke market makers
    """
    
    def __init__(
        self,
        wallet: Wallet,
        contract_config: ContractConfig,
        chain_config: ChainConfig,
    ):
        self.wallet = wallet
        self.contract_client = ContractClient(contract_config, chain_config)
    
    @property
    def address(self) -> str:
        """Get admin's Injective address."""
        return self.wallet.inj_address
    
    async def register_maker(self, maker_address: str) -> str:
        """Register a market maker.
        
        Args:
            maker_address: Injective address to register
            
        Returns:
            Transaction hash
        """
        logger.info(f"Registering maker: {maker_address}")
        return await self.contract_client.register_maker(
            private_key=self.wallet.private_key,
            maker_address=maker_address,
        )
    
    async def revoke_maker(self, maker_address: str) -> str:
        """Revoke a market maker.
        
        Args:
            maker_address: Injective address to revoke
            
        Returns:
            Transaction hash
        """
        logger.info(f"Revoking maker: {maker_address}")
        return await self.contract_client.revoke_maker(
            private_key=self.wallet.private_key,
            maker_address=maker_address,
        )
