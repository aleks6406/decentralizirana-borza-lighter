
import requests
from decimal import Decimal, InvalidOperation


API_BASE_URL = "https://mainnet.zklighter.elliot.ai/api/v1"


def _validate_order_side(orders, side_name):
    """Preveri cene in količine na eni strani order booka."""

    if not isinstance(orders, list):
        raise ValueError(f"Polje {side_name} mora biti seznam.")

    for index, order in enumerate(orders):
        if not isinstance(order, dict):
            raise ValueError(f"Vnos {index} v {side_name} mora biti slovar.")

        try:
            price = Decimal(str(order["price"]))
            quantity = Decimal(str(order["remaining_base_amount"]))
        except (KeyError, InvalidOperation, ValueError, TypeError):
            raise ValueError(f"Vnos {index} v {side_name} ima neveljavne številke.")

        if not price.is_finite() or price <= 0:
            raise ValueError(f"Cena v {side_name} mora biti končna in večja od nič.")
        if not quantity.is_finite() or quantity <= 0:
            raise ValueError(f"Količina v {side_name} mora biti končna in večja od nič.")


def get_orderbook(market_id, limit=10):
    """
    Pridobi nakupna in prodajna naročila za izbrani trg.

    Ob napaki povezave, odgovora HTTP ali podatkov
    izpiše razumljivo napako.
    """

    url = f"{API_BASE_URL}/orderBookOrders"

    params = {
        "market_id": market_id,
        "limit": limit
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as error:
            raise ValueError("API ni vrnil veljavnega JSON odgovora.") from error

        if not isinstance(data, dict):
            raise ValueError("Odgovor API-ja mora biti slovar.")

        if "asks" not in data or "bids" not in data:
            raise ValueError("Odgovor API-ja ne vsebuje asks in bids.")

        _validate_order_side(data["asks"], "asks")
        _validate_order_side(data["bids"], "bids")

        return {
            "asks": data["asks"],
            "bids": data["bids"]
        }

    except requests.exceptions.Timeout as error:
        raise RuntimeError(
            "API ni odgovoril v 10 sekundah."
        ) from error

    except requests.exceptions.ConnectionError as error:
        raise RuntimeError(
            "Povezava z API-jem ni uspela. "
            "Preveri internetno povezavo."
        ) from error

    except requests.exceptions.HTTPError as error:
        raise RuntimeError(
            f"API je vrnil napako HTTP: {error}"
        ) from error

    except ValueError as error:
        raise RuntimeError(
            f"Odgovor API-ja ni veljaven: {error}"
        ) from error
