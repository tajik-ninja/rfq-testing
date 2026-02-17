"""Shared setup utilities for chain authz grants and MM whitelist."""

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rfq_test.clients.chain import ChainClient
    from rfq_test.clients.contract import ContractClient
    from rfq_test.crypto.wallet import Wallet

logger = logging.getLogger(__name__)

# Authz message types required for retail/taker wallets
RETAIL_AUTHZ_GRANTS = [
    "/cosmos.bank.v1beta1.MsgSend",
    "/injective.exchange.v2.MsgPrivilegedExecuteContract",
    "/injective.exchange.v2.MsgBatchUpdateOrders",
    "/injective.exchange.v2.MsgCreateDerivativeMarketOrder",
]

# Authz message types required for MM wallets
MM_AUTHZ_GRANTS = [
    "/cosmos.bank.v1beta1.MsgSend",
    "/injective.exchange.v2.MsgPrivilegedExecuteContract",
]


async def setup_authz_grants(
    chain_client: "ChainClient",
    wallet: "Wallet",
    contract_address: str,
    msg_types: list[str],
) -> None:
    """Grant authz permissions for a wallet to the RFQ contract."""
    for msg_type in msg_types:
        try:
            tx_hash = await chain_client.grant_authz(
                private_key=wallet.private_key,
                grantee=contract_address,
                msg_type=msg_type,
            )
            logger.info(
                f"Granted {msg_type.split('.')[-1]} for {wallet.inj_address[:20]}...: {tx_hash}"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "authorization already exists" in error_msg:
                logger.debug(
                    f"Authz {msg_type.split('.')[-1]} already exists for {wallet.inj_address[:20]}..."
                )
            else:
                logger.warning(f"Failed to grant {msg_type.split('.')[-1]}: {e}")
                raise
        await asyncio.sleep(0.3)


async def ensure_mm_whitelisted(
    contract_client: "ContractClient",
    admin_private_key: str,
    mm_address: str,
) -> None:
    """Ensure MM is whitelisted on the RFQ contract."""
    try:
        is_registered = await contract_client.is_maker_registered(mm_address)
        if is_registered:
            logger.debug(f"MM {mm_address[:20]}... already whitelisted")
            return

        tx_hash = await contract_client.register_maker(admin_private_key, mm_address)
        logger.info(f"Whitelisted MM {mm_address[:20]}...: {tx_hash}")
        await asyncio.sleep(0.5)
    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg:
            logger.debug(f"MM {mm_address[:20]}... already whitelisted")
        else:
            logger.warning(f"Failed to whitelist MM: {e}")
            raise


async def ensure_subaccount_funded(
    chain_client: "ChainClient",
    wallet: "Wallet",
    amount_inj: float = 1000.0,
) -> None:
    """Deposit INJ from bank to exchange subaccount so the wallet can settle derivative trades.

    Call this for taker and maker wallets when tests expect accept_quote to settle on-chain.
    Wallets must have bank balance first (e.g. from faucet or fund step).
    """
    amount_wei = str(int(amount_inj * 1e18))
    try:
        tx_hash = await chain_client.deposit_to_subaccount(
            private_key=wallet.private_key,
            sender_address=wallet.inj_address,
            amount_wei=amount_wei,
            denom="inj",
        )
        logger.info(f"Funded subaccount for {wallet.inj_address[:20]}...: {tx_hash[:16]}...")
        await asyncio.sleep(0.5)
    except Exception as e:
        error_msg = str(e).lower()
        if "insufficient" in error_msg or "balance" in error_msg:
            logger.warning(
                f"Could not fund subaccount for {wallet.inj_address[:20]}... (no bank balance?). "
                "Run faucet/fund_subaccounts or use pre-funded wallet indices."
            )
        raise
