
from importlib import import_module
from decimal import Decimal, ROUND_HALF_UP


# Naložimo potrebne module.
markets_module = import_module("02_list_markets")
orderbook_module = import_module("03_get_orderbook")
spread_module = import_module("04_calculate_spread")
live_module = import_module("05_live_prices")
currency_module = import_module("06_currency_conversion")
connection_module = import_module("01_test_connection")
orders_module = import_module("orders")


def format_eur(value):
    """Pretvori vrednost v EUR in jo zaokroži na dva decimalna mesta."""

    value = Decimal(str(value))

    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def show_orderbook(market):
    """
    Pridobi order book in prikaže cene ter spread v EUR.
    """

    market_id = market["market_id"]
    quote_currency = markets_module.get_quote_currency(market)
    orderbook = orderbook_module.get_orderbook(market_id, limit=10)

    asks = orderbook["asks"]
    bids = orderbook["bids"]

    if not asks or not bids:
        print("Ni dovolj naročil za izračun spreada.")
        return

    # Izračun najboljših cen in spreada v izvorni valuti.
    result = spread_module.calculate_spread(asks, bids)

    print()
    print("=== POVZETEK TRGA ===")
    print(f"Kotacijska valuta:    {quote_currency}")

    if quote_currency == "USD":
        rate = currency_module.get_usd_to_eur_rate()
        best_ask = format_eur(result["best_ask"] * rate)
        best_bid = format_eur(result["best_bid"] * rate)
        spread = format_eur((result["best_ask"] - result["best_bid"]) * rate)
        print(f"Menjalni tečaj:       1 USD = {rate:.6f} EUR")
        print(f"Najboljša prodajna:   {best_ask:.2f} EUR")
        print(f"Najboljša nakupna:    {best_bid:.2f} EUR")
        print(f"Spread:               {spread:.2f} EUR")
    else:
        print("EUR pretvorba je na voljo samo za USD trge.")
        print(f"Najboljša prodajna:   {result['best_ask']} {quote_currency}")
        print(f"Najboljša nakupna:    {result['best_bid']} {quote_currency}")
        print(f"Spread:               {result['spread']} {quote_currency}")

    print(f"Spread (%):           {result['spread_percent']:.6f}%")

    print()
    print("=== PRODAJNA NAROČILA (ASKS) ===")

    for order in asks:
        if quote_currency == "USD":
            rate = currency_module.get_usd_to_eur_rate()
            price = format_eur(Decimal(str(order["price"])) * rate)
            currency = "EUR"
        else:
            price = order["price"]
            currency = quote_currency

        print(
            f"Cena: {price} {currency} | "
            f"Količina: {order['remaining_base_amount']}"
        )

    print()
    print("=== NAKUPNA NAROČILA (BIDS) ===")

    for order in bids:
        if quote_currency == "USD":
            rate = currency_module.get_usd_to_eur_rate()
            price = format_eur(Decimal(str(order["price"])) * rate)
            currency = "EUR"
        else:
            price = order["price"]
            currency = quote_currency

        print(
            f"Cena: {price} {currency} | "
            f"Količina: {order['remaining_base_amount']}"
        )


def main():
    while True:
        print("\n=== DECENTRALIZIRANA BORZA LIGHTER ===")
        print("Izberi način delovanja:")
        print("1 - Preveri povezavo")
        print("2 - Prikaži trge")
        print("3 - Prikaži order book in spread")
        print("4 - Spremljaj cene")
        print("5 - Prikaži graf zgodovine")
        print("6 - Oddaj limitno naročilo na testnetu")
        print("7 - Preveri status naročila")
        print("8 - Prekliči odprto naročilo")
        print("0 - Izhod")

        choice = input("Tvoja izbira: ").strip()

        try:
            if choice == "1":
                connection_module.check_connection()
            elif choice == "2":
                for market in markets_module.get_markets():
                    print(market["market_id"], market["symbol"], market.get("market_type", ""))
            elif choice in ("3", "4"):
                symbol = input("Vnesi simbol trga: ").strip().upper()
                market = markets_module.find_market(symbol)
                if market is None:
                    print("Trg ni bil najden.")
                elif choice == "3":
                    show_orderbook(market)
                else:
                    quote_currency = markets_module.get_quote_currency(market)
                    live_module.monitor_market(
                        market["market_id"], orderbook_module.get_orderbook,
                        spread_module.calculate_spread, quote_currency=quote_currency
                    )
            elif choice == "5":
                import_module("07_plot_history").main()
            elif choice == "6":
                orders_module.submit_testnet_order()
            elif choice == "7":
                orders_module.check_order_status()
            elif choice == "8":
                orders_module.cancel_open_order()
            elif choice == "0":
                print("Program se je zaključil.")
                return
            else:
                print("Neveljavna izbira.")
        except KeyboardInterrupt:
            print("\nOperacija je bila ustavljena.")
        except Exception as error:
            print("Prišlo je do napake:", error)


if __name__ == "__main__":
    main()
