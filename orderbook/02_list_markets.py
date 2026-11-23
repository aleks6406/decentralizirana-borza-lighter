
import requests


def get_markets():
    """
    Pridobi seznam trgov iz Lighter API-ja.
    Vrne seznam trgov.
    """

    url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBooks"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError("API ni vrnil veljavnega JSON odgovora.") from error

    if not isinstance(data, dict):
        raise RuntimeError("Odgovor API-ja mora biti slovar.")

    markets = data.get("order_books")

    if not isinstance(markets, list):
        raise RuntimeError("Odgovor API-ja mora vsebovati seznam order_books.")

    for market in markets:
        if not isinstance(market, dict):
            raise RuntimeError("Vsak trg v odgovoru mora biti slovar.")

        market_id = market.get("market_id")
        if not isinstance(market_id, int) or isinstance(market_id, bool) or market_id < 0:
            raise RuntimeError("Trg mora imeti nenegativen celoštevilski market_id.")

        symbol = market.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            raise RuntimeError("Trg mora imeti neprazen besedilni symbol.")

    return markets


def find_market(symbol):
    """
    Poišče trg po oznaki, na primer BTC ali DOT.
    Vrne podatke o trgu ali None, če trg ne obstaja.
    """

    if not isinstance(symbol, str):
        raise ValueError("Oznaka trga mora biti besedilo.")

    markets = get_markets()

    for market in markets:
        if market["symbol"].upper() == symbol.upper():
            return market

    return None


def get_quote_currency(market):
    """Pridobi oznako kotacijske valute za izbrani trg."""

    asset_id = market.get("quote_asset_id")
    if not isinstance(asset_id, int):
        raise RuntimeError("API za trg ne podaja quote_asset_id.")

    url = "https://mainnet.zklighter.elliot.ai/api/v1/assetDetails"
    response = requests.get(url, params={"asset_id": asset_id}, timeout=10)
    response.raise_for_status()
    data = response.json()

    assets = data.get("asset_details") if isinstance(data, dict) else None
    if not isinstance(assets, list) or not assets or not isinstance(assets[0], dict):
        raise RuntimeError("API ni vrnil podatkov o kotacijski valuti.")

    if assets[0].get("asset_id") != asset_id:
        raise RuntimeError("API je vrnil podatke o napačni kotacijski valuti.")

    symbol = assets[0].get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise RuntimeError("API ni vrnil oznake kotacijske valute.")

    return symbol.upper()
