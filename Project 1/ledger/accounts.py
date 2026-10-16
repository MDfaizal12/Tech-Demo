"""Account models and transaction posting rules."""

from abc import ABC, abstractmethod
import math
import secrets
import threading


class BaseAccount(ABC):
    """Shared account state and validation for concrete account types."""

    def __init__(
        self,
        account_id: str,
        auth_token: str,
        opening_balance: float = 0.0,
    ) -> None:
        assert isinstance(account_id, str) and account_id.strip(), (
            "account_id must be a non-empty string"
        )
        assert isinstance(auth_token, str) and auth_token, (
            "auth_token must be a non-empty string"
        )
        assert isinstance(opening_balance, (int, float)) and not isinstance(
            opening_balance, bool
        ), "opening_balance must be numeric"
        assert math.isfinite(opening_balance), "opening_balance must be finite"

        self.account_id = account_id.strip()
        self._balance = float(opening_balance)
        self.__auth_token = auth_token
        self._lock = threading.RLock()

    def __del__(self) -> None:
        """Clear the private authentication token when the account is discarded."""
        self.__auth_token = ""

    @property
    def balance(self) -> float:
        """Return the current account balance in the ledger's base currency."""
        with self._lock:
            return self._balance

    def verify_auth_token(self, candidate: str) -> bool:
        """Compare a candidate token without exposing the stored token."""
        return isinstance(candidate, str) and secrets.compare_digest(
            self.__auth_token, candidate
        )

    @staticmethod
    def _validate_posting(amount: float, base_amount: float) -> None:
        for name, value in (("amount", amount), ("base_amount", base_amount)):
            assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                f"{name} must be numeric"
            )
            assert math.isfinite(value), f"{name} must be finite"
        assert (amount == 0 or base_amount == 0) or (
            (amount > 0) == (base_amount > 0)
        ), "amount and base_amount must have the same sign"

    @abstractmethod
    def post_transaction(self, amount: float, base_amount: float) -> None:
        """Post a transaction; balances are maintained in the base currency."""

    @abstractmethod
    def calculate_statement_fees(self) -> float:
        """Return the statement fee for this account, in the base currency."""


class SavingsAccount(BaseAccount):
    """Savings account that does not permit an overdrawn balance."""

    def post_transaction(self, amount: float, base_amount: float) -> None:
        self._validate_posting(amount, base_amount)
        with self._lock:
            updated_balance = self._balance + float(base_amount)
            if updated_balance < 0.0:
                raise ValueError(
                    f"Transaction would overdraw savings account {self.account_id}"
                )
            self._balance = updated_balance

    def calculate_statement_fees(self) -> float:
        return 0.0


class CorporateAccount(BaseAccount):
    """Corporate account with a revolving overdraft and monthly facility fee."""

    OVERDRAFT_LIMIT = -10_000.0
    MONTHLY_FACILITY_FEE = 25.0

    def post_transaction(self, amount: float, base_amount: float) -> None:
        self._validate_posting(amount, base_amount)
        with self._lock:
            updated_balance = self._balance + float(base_amount)
            if updated_balance < self.OVERDRAFT_LIMIT:
                raise ValueError(
                    f"Transaction exceeds the overdraft limit for account "
                    f"{self.account_id} ({self.OVERDRAFT_LIMIT:.2f})"
                )
            self._balance = updated_balance

    def calculate_statement_fees(self) -> float:
        return self.MONTHLY_FACILITY_FEE
