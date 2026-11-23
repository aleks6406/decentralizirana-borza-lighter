
from importlib import import_module
from decimal import Decimal, ROUND_HALF_UP


# Naložimo potrebne module.
markets_module = import_module("02_list_markets")
orderbook_module = import_module("03_get_orderbook")
spread_module = import_module("04_calculate_spread")
live_module = import_module("05_live_prices")
currency_module = import_module("06_currency_conversion")


def format_eur(value):
    """Pretvori vrednost v EUR in jo zaokroži na dva decimalna mesta."""

    value = Decimal(str(value))

    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def show_orderbook(market_id):
    """
    Pridobi order book in prikaže cene ter spread v EUR.
    """

    orderbook = orderbook_module.get_orderbook(
        market_id,
        limit=10
    )

    asks = orderbook["asks"]
    bids = orderbook["bids"]

    if not asks or not bids:
        print("Ni dovolj naročil za izračun spreada.")
        return

    # Izračun najboljših cen in spreada v izvorni valuti.
    result = spread_module.calculate_spread(asks, bids)

    # Pridobimo aktualni menjalni tečaj USD/EUR.
    rate = currency_module.get_usd_to_eur_rate()

    # Pretvorimo najboljši prodajni in nakupni tečaj.
    best_ask_eur = format_eur(result["best_ask"] * rate)
    best_bid_eur = format_eur(result["best_bid"] * rate)

    # Spread pretvorimo iz USD v EUR.
    spread_eur = format_eur(
        (result["best_ask"] - result["best_bid"]) * rate
    )

    print()
    print("=== POVZETEK TRGA ===")
    print(f"Menjalni tečaj:       1 USD = {rate:.6f} EUR")
    print(f"Najboljša prodajna:   {best_ask_eur:.2f} EUR")
    print(f"Najboljša nakupna:    {best_bid_eur:.2f} EUR")
    print(f"Spread:               {spread_eur:.2f} EUR")
    print(f"Spread (%):           {result['spread_percent']:.6f}%")

    print()
    print("=== PRODAJNA NAROČILA (ASKS) ===")

    for order in asks:
        price_eur = format_eur(
            Decimal(str(order["price"])) * rate
        )

        print(
            f"Cena: {price_eur:.2f} EUR | "
            f"Količina: {order['remaining_base_amount']}"
        )

    print()
    print("=== NAKUPNA NAROČILA (BIDS) ===")

    for order in bids:
        price_eur = format_eur(
            Decimal(str(order["price"])) * rate
        )

        print(
            f"Cena: {price_eur:.2f} EUR | "
            f"Količina: {order['remaining_base_amount']}"
        )


def main():
    print("=== LIGHTER ORDER BOOK ===")
    print()

    symbol = input(
        "Vnesi trg (npr. BTC ali DOT): "
    ).strip().upper()

    try:
        market = markets_module.find_market(symbol)

        if market is None:
            print(f"Trg {symbol} ni bil najden.")
            return

        market_id = market["market_id"]

        print()
        print("Izbrani trg:", market["symbol"])
        print("Market ID:", market_id)

        print()
        print("Izberi način delovanja:")
        print("1 - Enkratni prikaz order booka v EUR")
        print("2 - Spremljanje cen v živo")
        print("0 - Izhod")

        choice = input("Tvoja izbira: ").strip()

        if choice == "1":
            show_orderbook(market_id)

        elif choice == "2":
            live_module.monitor_market(
                market_id=market_id,
                get_orderbook=orderbook_module.get_orderbook,
                calculate_spread=spread_module.calculate_spread,
                interval=3,
                limit=10
            )

        elif choice == "0":
            print("Program se je zaključil.")

        else:
            print("Neveljavna izbira. Zaženi program in poskusi znova.")

    except KeyboardInterrupt:
        print()
        print("Program je bil ustavljen.")

    except Exception as error:
        print("Prišlo je do napake:", error)


if __name__ == "__main__":
    main()
