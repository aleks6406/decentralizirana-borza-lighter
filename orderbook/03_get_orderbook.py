
import requests


API_BASE_URL = "https://mainnet.zklighter.elliot.ai/api/v1"


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
        data = response.json()

        if "asks" not in data or "bids" not in data:
            raise ValueError(
                "Odgovor API-ja ne vsebuje asks in bids."
            )

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
