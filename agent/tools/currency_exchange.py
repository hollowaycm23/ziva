"""
Currency Exchange Rate Tool
Fetches real-time currency exchange rates.
"""

import requests
from typing import Dict
from datetime import datetime


def get_exchange_rate(
    from_currency: str = "USD",
    to_currency: str = "BRL",
    amount: float = 1.0
) -> Dict:
    """
    Get real-time currency exchange rates.

    Args:
        from_currency: Source currency code (e.g., "USD", "EUR", "GBP")
        to_currency: Target currency code (e.g., "BRL", "USD", "EUR")
        amount: Amount to convert (default: 1.0)

    Returns:
        Dictionary with exchange rate information:
        {
            "base_currency": str,
            "target_currency": str,
            "rate": float,
            "amount": float,
            "converted_amount": float,
            "timestamp": str,
            "source": str
        }

    Examples:
        >>> get_exchange_rate("USD", "BRL")
        {"base_currency": "USD", "target_currency": "BRL", "rate": 5.39, ...}

        >>> get_exchange_rate("EUR", "USD", 100)
        {"amount": 100, "converted_amount": 110.5, ...}
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    try:
        # Primary API: ExchangeRate-API (free, no key required)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        # Check if target currency exists in rates
        if to_currency not in data.get("rates", {}):
            return {
                "error": f"Currency code '{to_currency}' not found",
                "available_currencies": list(data.get("rates", {}).keys())[:20]
            }

        rate = data["rates"][to_currency]
        converted = amount * rate

        return {
            "success": True,
            "base_currency": from_currency,
            "target_currency": to_currency,
            "rate": round(
                rate,
                4),
            "amount": amount,
            "converted_amount": round(
                converted,
                2),
            "timestamp": datetime.now().isoformat(),
            "source": "ExchangeRate-API",
            "formatted": f"{amount} {from_currency} = {
                converted:.2f} {to_currency}"}

    except requests.exceptions.RequestException as e:
        # Fallback: Try alternative API
        try:
            return _get_rate_fallback(from_currency, to_currency, amount)
        except Exception as fallback_e:
            return {
                "success": False,
                "error": f"Failed to fetch exchange rate: {
                    str(e)} and {
                    str(fallback_e)}",
                "base_currency": from_currency,
                "target_currency": to_currency}


def _get_rate_fallback(from_currency: str, to_currency: str,
                       amount: float) -> Dict:
    """Fallback API if primary fails"""
    # Alternative: frankfurter.app (European Central Bank rates)
    if from_currency == to_currency:
        return {
            "success": True,
            "base_currency": from_currency,
            "target_currency": to_currency,
            "rate": 1.0,
            "amount": amount,
            "converted_amount": amount,
            "timestamp": datetime.now().isoformat(),
            "source": "Same currency",
            "formatted": f"{amount} {from_currency} = {amount} {to_currency}"
        }

    url = f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"

    response = requests.get(url, timeout=5)
    response.raise_for_status()

    data = response.json()
    rate = data["rates"][to_currency]
    converted = amount * rate

    return {
        "success": True,
        "base_currency": from_currency,
        "target_currency": to_currency,
        "rate": round(
            rate,
            4),
        "amount": amount,
        "converted_amount": round(
            converted,
            2),
        "timestamp": datetime.now().isoformat(),
        "source": "Frankfurter (ECB)",
        "formatted": f"{amount} {from_currency} = {
            converted:.2f} {to_currency}"}


def get_currency_info(currency_code: str) -> Dict:
    """
    Get information about a specific currency.

    Args:
        currency_code: Currency code (e.g., "BRL", "USD", "EUR")

    Returns:
        Dictionary with currency information
    """
    # Common currency information
    currencies = {
        "USD": {"name": "US Dollar", "symbol": "$", "country": "United States"},
        "BRL": {"name": "Brazilian Real", "symbol": "R$", "country": "Brazil"},
        "EUR": {"name": "Euro", "symbol": "€", "country": "European Union"},
        "GBP": {"name": "British Pound", "symbol": "£", "country": "United Kingdom"},
        "JPY": {"name": "Japanese Yen", "symbol": "¥", "country": "Japan"},
        "CNY": {"name": "Chinese Yuan", "symbol": "¥", "country": "China"},
        "ARS": {"name": "Argentine Peso", "symbol": "$", "country": "Argentina"},
        "MXN": {"name": "Mexican Peso", "symbol": "$", "country": "Mexico"},
        "CAD": {"name": "Canadian Dollar", "symbol": "C$", "country": "Canada"},
        "AUD": {"name": "Australian Dollar", "symbol": "A$", "country": "Australia"},
    }

    currency_code = currency_code.upper()

    if currency_code in currencies:
        info = currencies[currency_code]
        info["code"] = currency_code
        return {"success": True, **info}
    else:
        return {
            "success": False,
            "error": f"Currency '{currency_code}' not in database",
            "available": list(currencies.keys())
        }


# For tool registration
TOOL_METADATA = {
    "name": "get_exchange_rate",
    "description": "Get real-time currency exchange rates between any two currencies",
    "parameters": {
        "from_currency": {
            "type": "string",
            "description": "Source currency code (e.g., USD, EUR, GBP)",
            "default": "USD"
        },
        "to_currency": {
            "type": "string",
            "description": "Target currency code (e.g., BRL, USD, EUR)",
            "default": "BRL"
        },
        "amount": {
            "type": "number",
            "description": "Amount to convert",
            "default": 1.0
        }
    },
    "returns": {
        "type": "object",
        "description": "Exchange rate data with conversion result"
    }
}


if __name__ == "__main__":
    # Test the tool
    print("🧪 Testing Currency Exchange Tool\n")

    # Test 1: USD to BRL
    print("1. USD to BRL:")
    result = get_exchange_rate("USD", "BRL")
    print(f"   {result.get('formatted', result)}\n")

    # Test 2: EUR to USD with amount
    print("2. 100 EUR to USD:")
    result = get_exchange_rate("EUR", "USD", 100)
    print(f"   {result.get('formatted', result)}\n")

    # Test 3: Currency info
    print("3. BRL Info:")
    info = get_currency_info("BRL")
    print(f"   {info}\n")

    # Test 4: Invalid currency
    print("4. Error handling (invalid currency):")
    result = get_exchange_rate("USD", "INVALID")
    print(f"   {result.get('error', 'No error')}\n")
