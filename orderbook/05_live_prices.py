
import time
import os
import csv
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP


currency_module = __import__(
    "06_currency_conversion",
    fromlist=["get_usd_to_eur_rate"]
)


# CSV datoteka bo shranjena v isti mapi kot ta Python datoteka.
CSV_FILE = Path(__file__).resolve().parent / "price_history.csv"


# Stolpci v datoteki CSV.
CSV_COLUMNS = [
    "timestamp",
    "market_id",
    "best_bid",
    "best_ask",
    "spread",
    "spread_percent",
    "usd_to_eur_rate",
    "best_bid_eur",
    "best_ask_eur",
    "spread_eur"
]


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def format_eur(value):
    """Zaokroži vrednost v EUR na dve decimalni mesti."""

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def save_price_history(
    market_id,
    result,
    rate,
    best_bid_eur,
    best_ask_eur,
    spread_eur
):
    """
    Shrani uspešno meritev cen in spreada v CSV.

    Če datoteka še ne obstaja, ustvari datoteko
    in vanjo najprej zapiše imena stolpcev.
    """

    file_exists = CSV_FILE.exists() and CSV_FILE.stat().st_size > 0

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market_id,
        "best_bid": str(result["best_bid"]),
        "best_ask": str(result["best_ask"]),
        "spread": str(result["spread"]),
        "spread_percent": str(result["spread_percent"]),
        "usd_to_eur_rate": str(rate),
        "best_bid_eur": str(best_bid_eur),
        "best_ask_eur": str(best_ask_eur),
        "spread_eur": str(spread_eur)
    }

    with CSV_FILE.open(
        mode="a",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_COLUMNS
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def monitor_market(
    market_id,
    get_orderbook,
    calculate_spread,
    interval=3,
    limit=10
):
    """Spremlja order book, prikazuje cene v EUR in shranjuje zgodovino."""

    try:
        while True:
            clear_screen()

            print("=== LIGHTER | CENE V ŽIVO (EUR) ===")
            print(f"Čas: {time.strftime('%H:%M:%S')}")
            print("-" * 40)

            try:
                orderbook = get_orderbook(
                    market_id,
                    limit=limit
                )

                asks = orderbook["asks"]
                bids = orderbook["bids"]

                if not asks or not bids:
                    print("Ni dovolj naročil za prikaz.")

                else:
                    result = calculate_spread(asks, bids)
                    rate = currency_module.get_usd_to_eur_rate()

                    best_ask_eur = format_eur(
                        result["best_ask"] * rate
                    )

                    best_bid_eur = format_eur(
                        result["best_bid"] * rate
                    )

                    spread_eur = format_eur(
                        (
                            result["best_ask"]
                            - result["best_bid"]
                        ) * rate
                    )

                    # Shranimo uspešno meritev v CSV.
                    try:
                        save_price_history(
                            market_id=market_id,
                            result=result,
                            rate=rate,
                            best_bid_eur=best_bid_eur,
                            best_ask_eur=best_ask_eur,
                            spread_eur=spread_eur
                        )

                        print("Zgodovina: meritev shranjena v CSV.")

                    except (OSError, csv.Error) as error:
                        print("Napaka pri shranjevanju zgodovine:")
                        print(error)

                    print()
                    print(f"Menjalni tečaj: 1 USD = {rate:.6f} EUR")
                    print()

                    print(
                        f"Najboljša prodajna: {best_ask_eur:.2f} EUR"
                    )

                    print(
                        f"Najboljša nakupna:  {best_bid_eur:.2f} EUR"
                    )

                    print(f"Spread:             {spread_eur:.2f} EUR")

                    print(
                        f"Spread (%):         "
                        f"{result['spread_percent']:.6f}%"
                    )

            except Exception as error:
                print("Napaka pri pridobivanju ali pretvorbi podatkov:")
                print(error)
                print("Program bo poskusil znova.")

            print()
            print(f"Osveževanje vsakih {interval} sekund")
            print("Za ustavitev pritisni Ctrl+C.")

            time.sleep(interval)

    except KeyboardInterrupt:
        clear_screen()
        print("Spremljanje je ustavljeno.")
