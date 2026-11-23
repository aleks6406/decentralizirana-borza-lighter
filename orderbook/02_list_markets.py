
import requests


def get_markets():
    """
    Pridobi seznam trgov iz Lighter API-ja.
    Vrne seznam trgov.
    """

    url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBooks"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    return data["order_books"]


def find_market(symbol):
    """
    Poišče trg po oznaki, na primer BTC ali DOT.
    Vrne podatke o trgu ali None, če trg ne obstaja.
    """

    markets = get_markets()

    for market in markets:
        if market["symbol"].upper() == symbol.upper():
            return market

    return None
