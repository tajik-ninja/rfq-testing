"""Custom exceptions for RFQ testing.

We use exception types (not messages) for assertions,
making tests resilient to error message changes.
"""


class RFQTestError(Exception):
    """Base exception for all RFQ test errors."""
    pass


# ============================================================
# Indexer Errors
# ============================================================

class IndexerError(RFQTestError):
    """Base exception for Indexer-related errors."""
    pass


class IndexerConnectionError(IndexerError):
    """Failed to connect to Indexer WebSocket."""
    pass


class IndexerValidationError(IndexerError):
    """Indexer rejected input due to validation failure."""
    pass


class IndexerTimeoutError(IndexerError):
    """Timeout waiting for Indexer response."""
    pass


# ============================================================
# Contract Errors
# ============================================================

class ContractError(RFQTestError):
    """Base exception for Contract-related errors."""
    pass


class ContractExecutionError(ContractError):
    """Contract execution failed."""
    pass


class ContractUnauthorizedError(ContractError):
    """Unauthorized action on contract."""
    pass


class ContractValidationError(ContractError):
    """Contract rejected input due to validation."""
    pass


# ============================================================
# Chain Errors
# ============================================================

class ChainError(RFQTestError):
    """Base exception for Chain-related errors."""
    pass


class ChainConnectionError(ChainError):
    """Failed to connect to chain."""
    pass


class ChainTimeoutError(ChainError):
    """Timeout waiting for chain confirmation."""
    pass


class InsufficientFundsError(ChainError):
    """Wallet has insufficient funds."""
    pass


# ============================================================
# Wallet Errors
# ============================================================

class WalletError(RFQTestError):
    """Base exception for Wallet-related errors."""
    pass


class WalletNotFundedError(WalletError):
    """Wallet not funded."""
    pass


class FaucetError(WalletError):
    """Failed to get funds from faucet."""
    pass
