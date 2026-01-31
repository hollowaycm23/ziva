"""
Currency Exchange Rate Tool for Ziva
Fetches real-time currency exchange rates.
"""

import requests
from datetime import datetime


def get_exchange_rate(from_currency: str = "USD",
                      to_currency: str = "BRL", amount: float = 1.0) -> dict:
    """
    Obtém cotações de moedas em tempo real.

    Use esta ferramenta quando o usuário perguntar sobre:
    - Valor/cotação do dólar, euro, ou outra moeda
    - Conversão entre moedas
    - "Quanto está o dólar hoje?"
    - "Converter X dólares para reais"

    Args:
        from_currency: Moeda de origem (USD, EUR, GBP, etc.)
        to_currency: Moeda de destino (BRL, USD, EUR, etc.)
        amount: Quantidade a converter (padrão: 1.0)

    Returns:
        dict: Dados da cotação com valor convertido
    """

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    try:
        # API primária: ExchangeRate-API (gratuita, sem chave)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        if to_currency not in data.get("rates", {}):
            return {
                "error": f"Moeda '{to_currency}' não encontrada",
                "available": list(data.get("rates", {}).keys())[:20]
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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "ExchangeRate-API",
            "formatted": f"{amount} {from_currency} = {
                converted:.2f} {to_currency}",
            "message": f"Hoje, {amount} {from_currency} equivale a R$ {
                    converted:.2f} {to_currency}. Taxa: 1 {from_currency} = {
                        rate:.4f} {to_currency}"}

    except Exception as e:
        # Fallback API
        try:
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
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Frankfurter (ECB)",
                "formatted": f"{amount} {from_currency} = {
                    converted:.2f} {to_currency}",
                "message": f"Hoje, {amount} {from_currency} equivale a {
                    converted:.2f} {to_currency}. Taxa: 1 {from_currency} = {
                        rate:.4f} {to_currency}"}
        except BaseException:
            return {
                "success": False,
                "error": f"Falha ao obter cotação: {
                    str(e)}",
                "message": "Não foi possível obter a cotação no momento. Tente novamente."}


# Marcar como ferramenta Ziva
get_exchange_rate._is_ziva_tool = True
