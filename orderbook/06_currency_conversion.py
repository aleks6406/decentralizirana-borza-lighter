
import time
import requests
from decimal import Decimal, InvalidOperation


API_URL = "https://open.er-api.com/v6/latest/USD"

# Menjalni tečaj shranimo za 5 minut,
# da ga ne zahtevamo ob vsaki osvežitvi cen.
_cached_rate = None
_last_update = 0
CACHE_SECONDS = 300


def get_usd_to_eur_rate():
    """
    Pridobi aktualni menjalni tečaj USD v EUR.
    Tečaj pred ponovnim pridobivanjem hranimo 5 minut.
    """

    global _cached_rate, _last_update

    current_time = time.time()

    if (
        _cached_rate is not None
        and current_time - _last_update < CACHE_SECONDS
    ):
        return _cached_rate

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict) or data.get("result") != "success":
            raise RuntimeError(
                "Vir menjalnih tečajev ni vrnil uspešnega odgovora."
            )

        rates = data.get("rates")
        if not isinstance(rates, dict) or "EUR" not in rates:
            raise RuntimeError("Odgovor ne vsebuje menjalnega tečaja EUR.")

        rate = rates["EUR"]
        rate = Decimal(str(rate))
        if not rate.is_finite() or rate <= 0:
            raise RuntimeError("Vir je vrnil neveljaven menjalni tečaj.")

        _cached_rate = rate
        _last_update = current_time

        return _cached_rate

    except (requests.RequestException, KeyError, ValueError, TypeError, InvalidOperation) as error:
        raise RuntimeError(
            f"Menjalnega tečaja USD/EUR ni bilo mogoče pridobiti: {error}"
        ) from error


def convert_to_eur(price_usd):
    """
    Pretvori ceno iz USD v EUR.
    """

    rate = get_usd_to_eur_rate()
    price = Decimal(str(price_usd))

    return price * rate


if __name__ == "__main__":
    try:
        rate = get_usd_to_eur_rate()

        print("=== MENJALNI TEČAJ ===")
        print(f"1 USD = {rate:.6f} EUR")

        example_price = Decimal("1000")
        converted_price = convert_to_eur(example_price)

        print()
        print(f"Primer: 1000 USD = {converted_price:.2f} EUR")

    except RuntimeError as error:
        print("Napaka:", error)
