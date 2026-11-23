
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _validate_orders(orders, side_name):
    """Preveri, da imajo vnosi veljavno ceno in količino."""

    if not isinstance(orders, list):
        raise ValueError(f"Seznam {side_name} mora biti seznam.")

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


def calculate_spread(asks, bids):
    """
    Izračuna najboljšo prodajno in nakupno ceno ter spread.

    Najboljša prodajna cena je najnižja cena v asks.
    Najboljša nakupna cena je najvišja cena v bids.

    Spread zaokroži na tri decimalna mesta.
    Odstotni spread zaokroži na šest decimalnih mest.
    """

    _validate_orders(asks, "asks")
    _validate_orders(bids, "bids")

    if not asks or not bids:
        raise ValueError(
            "Za izračun potrebujemo nakupna in prodajna naročila."
        )

    # Poiščemo najnižjo prodajno ceno.
    best_ask_order = min(
        asks,
        key=lambda order: Decimal(str(order["price"]))
    )

    # Poiščemo najvišjo nakupno ceno.
    best_bid_order = max(
        bids,
        key=lambda order: Decimal(str(order["price"]))
    )

    best_ask = Decimal(str(best_ask_order["price"]))
    best_bid = Decimal(str(best_bid_order["price"]))

    if best_bid > best_ask:
        raise ValueError(
            f"Prekrižan order book: best bid ({best_bid}) je višji od best ask ({best_ask})."
        )

    # Izračunamo spread brez predhodnega zaokroževanja.
    raw_spread = best_ask - best_bid

    # Spread za prikaz zaokrožimo na tri decimalna mesta.
    spread = raw_spread.quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP
    )

    # Izračunamo odstotni spread.
    spread_percent = (raw_spread / best_bid) * Decimal("100")

    # Odstotni spread zaokrožimo na šest decimalnih mest.
    spread_percent = spread_percent.quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP
    )

    return {
        "best_ask": best_ask,
        "best_bid": best_bid,
        "spread": spread,
        "spread_percent": spread_percent
    }
