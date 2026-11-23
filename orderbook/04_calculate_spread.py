
from decimal import Decimal, ROUND_HALF_UP


def calculate_spread(asks, bids):
    """
    Izračuna najboljšo prodajno in nakupno ceno ter spread.

    Najboljša prodajna cena je najnižja cena v asks.
    Najboljša nakupna cena je najvišja cena v bids.

    Spread zaokroži na tri decimalna mesta.
    Odstotni spread zaokroži na šest decimalnih mest.
    """

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

    # Izračunamo spread brez predhodnega zaokroževanja.
    raw_spread = best_ask - best_bid

    # Spread za prikaz zaokrožimo na tri decimalna mesta.
    spread = raw_spread.quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP
    )

    # Izračunamo odstotni spread.
    if best_bid == 0:
        spread_percent = Decimal("0")
    else:
        spread_percent = (
            raw_spread / best_bid
        ) * Decimal("100")

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
