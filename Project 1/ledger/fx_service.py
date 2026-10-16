"""Live foreign exchange conversion with an offline fallback."""

import math
import threading
from typing import Any

import requests


class CurrencyConverter:
    """Convert transaction amounts into USD using live rates when available.

    The offline table stores units of each currency per one USD. For example,
    0.92 EUR per USD means a EUR amount is divided by 0.92 to obtain USD.
    """

    API_URL = "https://open.er-api.com/v6/latest/USD"
    REQUEST_TIMEOUT_SECONDS = 5
    OFFLINE_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "INR": 83.0,
        "CAD": 1.36,
        "JPY": 149.0,
    }

    def __init__(self, timeout: float = REQUEST_TIMEOUT_SECONDS) -> None:
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
            raise TypeError("timeout must be a positive number")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number")
        self.timeout = float(timeout)
        self._rates: dict[str, Any] | None = None
        self._offline_mode = False
        self._rate_lock = threading.Lock()

    def _fetch_usd_rates(self) -> dict[str, Any]:
        with self._rate_lock:
            if self._rates is not None:
                return self._rates
            if self._offline_mode:
                raise requests.ConnectionError("Using cached offline exchange rates")
            try:
                response = requests.get(self.API_URL, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                if payload.get("result") != "success":
                    raise KeyError(
                        "Exchange-rate service did not return a successful result"
                    )
                self._rates = payload["rates"]
                return self._rates
            except requests.RequestException:
                self._offline_mode = True
                raise
            except KeyError:
                self._offline_mode = True
                raise

    def convert_to_base(self, amount: float, source_currency: str) -> float:
        """Convert an amount to USD and round the result to two decimal places."""
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("amount must be numeric")
        if not math.isfinite(amount):
            raise ValueError("amount must be finite")
        if not isinstance(source_currency, str) or not source_currency.strip():
            raise ValueError("source_currency must be a non-empty currency code")

        currency = source_currency.strip().upper()
        if self._offline_mode:
            return round(float(amount) / self._offline_rate(currency), 2)

        try:
            try:
                rates = self._fetch_usd_rates()
                usd_rate = float(rates[currency])
                if not math.isfinite(usd_rate):
                    raise ValueError(f"Invalid live exchange rate for {currency}")
                converted = float(amount) / usd_rate
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                converted = float(amount) / self.OFFLINE_RATES[currency]
        except requests.RequestException:
            converted = float(amount) / self._offline_rate(currency)
        except KeyError as exc:
            raise ValueError(
                f"Unsupported currency code: {currency}"
            ) from exc
        except ZeroDivisionError:
            converted = float(amount) / self._offline_rate(currency)

        return round(converted, 2)

    def _offline_rate(self, currency: str) -> float:
        """Return a supported offline rate with an actionable error on misses."""
        try:
            return self.OFFLINE_RATES[currency]
        except KeyError as exc:
            raise ValueError(f"Unsupported currency code: {currency}") from exc
