
import csv
import math
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation


CSV_FILE = Path(__file__).resolve().parent / "price_history.csv"
REFRESH_INTERVAL = 3000  # 3 sekunde v milisekundah

BACKGROUND = "#000000"
TEXT_COLOR = "#FFFFFF"
GRID_COLOR = "#444444"

BUY_COLOR = "#FF3333"
SELL_COLOR = "#00E676"
SPREAD_COLOR = "#00BFFF"
PERCENT_COLOR = "#FFB74D"


def load_history():
    """Prebere zgodovino meritev iz CSV."""

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Datoteka ne obstaja: {CSV_FILE}"
        )

    with CSV_FILE.open(
        mode="r",
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def choose_market(rows):
    """Omogoči izbiro trga."""

    market_ids = sorted({
        row["market_id"]
        for row in rows
        if row.get("market_id")
    })

    if not market_ids:
        raise ValueError(
            "CSV ne vsebuje meritev. Najprej zaženi spremljanje cen."
        )

    print("\n=== IZBIRA TRGA ===")

    for market_id in market_ids:
        count = sum(
            1 for row in rows
            if row.get("market_id") == market_id
        )
        print(f"Market ID {market_id}: {count} meritev")

    while True:
        selected = input("\nVnesi Market ID: ").strip()

        if selected in market_ids:
            return selected

        print("Neveljaven ID. Poskusi znova.")


def prepare_data(rows, market_id):
    """Pripravi in časovno razvrsti podatke."""

    data = []

    for row in rows:
        if row.get("market_id") != market_id:
            continue

        try:
            values = (
                float(row["best_bid_eur"]),
                float(row["best_ask_eur"]),
                float(row["spread_eur"]),
                float(row["spread_percent"]),
            )
            if (
                not all(math.isfinite(value) for value in values)
                or values[0] <= 0
                or values[1] <= 0
                or values[2] < 0
                or values[3] < 0
            ):
                continue

            data.append((datetime.fromisoformat(row["timestamp"]), *values))
        except (KeyError, ValueError, TypeError):
            continue

    data.sort(key=lambda item: item[0])

    if not data:
        return None

    return tuple(
        [item[index] for item in data]
        for index in range(5)
    )


def style_axes(fig, axes):
    """Nastavi črno ozadje in berljivo besedilo."""

    fig.patch.set_facecolor(BACKGROUND)

    for ax in axes:
        ax.set_facecolor(BACKGROUND)
        ax.tick_params(colors=TEXT_COLOR)

        ax.xaxis.label.set_color(TEXT_COLOR)
        ax.yaxis.label.set_color(TEXT_COLOR)
        ax.title.set_color(TEXT_COLOR)

        for spine in ax.spines.values():
            spine.set_color(GRID_COLOR)

        ax.grid(
            True,
            color=GRID_COLOR,
            linestyle="--",
            linewidth=0.6,
            alpha=0.8
        )

        legend = ax.legend(
            facecolor="#151515",
            edgecolor=GRID_COLOR
        )

        for label in legend.get_texts():
            label.set_color(TEXT_COLOR)


def main():
    try:
        rows = load_history()
        market_id = choose_market(rows)

        initial_data = prepare_data(rows, market_id)

        if initial_data is None:
            raise ValueError(
                "Za izbrani trg ni veljavnih meritev."
            )

        fig, axes = plt.subplots(
            3, 1,
            figsize=(13, 10),
            sharex=True
        )

        fig.suptitle(
            f"LIGHTER | ZGODOVINA TRGA {market_id}",
            fontsize=16,
            fontweight="bold",
            color=TEXT_COLOR
        )

        def update(_frame):
            """Vsake 3 sekunde ponovno prebere CSV in posodobi grafe."""

            try:
                latest_rows = load_history()
                data = prepare_data(latest_rows, market_id)

                if data is None:
                    return

                (
                    timestamps,
                    best_bids,
                    best_asks,
                    spreads_eur,
                    spreads_percent
                ) = data

                for ax in axes:
                    ax.clear()

                # 1. Nakupna in prodajna cena.
                axes[0].plot(
                    timestamps,
                    best_bids,
                    color=BUY_COLOR,
                    label="Najboljša nakupna cena",
                    linewidth=2
                )

                axes[0].plot(
                    timestamps,
                    best_asks,
                    color=SELL_COLOR,
                    label="Najboljša prodajna cena",
                    linewidth=2
                )

                axes[0].set_title(
                    "NAKUPNA IN PRODAJNA CENA",
                    fontweight="bold"
                )
                axes[0].set_ylabel("Cena (EUR)")

                # 2. Spread v EUR.
                axes[1].plot(
                    timestamps,
                    spreads_eur,
                    color=SPREAD_COLOR,
                    label="Spread v EUR",
                    linewidth=2
                )

                axes[1].set_title(
                    "SPREAD V EVRIH",
                    fontweight="bold"
                )
                axes[1].set_ylabel("Spread (EUR)")

                # 3. Spread v odstotkih.
                axes[2].plot(
                    timestamps,
                    spreads_percent,
                    color=PERCENT_COLOR,
                    label="Spread v %",
                    linewidth=2
                )

                axes[2].set_title(
                    "SPREAD V ODSTOTKIH",
                    fontweight="bold"
                )
                axes[2].set_ylabel("Spread (%)")
                axes[2].set_xlabel("Čas meritve")

                axes[2].xaxis.set_major_formatter(
                    mdates.DateFormatter("%H:%M:%S")
                )
                axes[2].xaxis.set_major_locator(
                    mdates.AutoDateLocator()
                )

                for label in axes[2].get_xticklabels():
                    label.set_rotation(30)
                    label.set_ha("right")

                style_axes(fig, axes)

                fig.suptitle(
                    f"LIGHTER | TRG {market_id} | "
                    f"{len(timestamps)} meritev",
                    fontsize=16,
                    fontweight="bold",
                    color=TEXT_COLOR
                )

                fig.tight_layout(rect=[0, 0, 1, 0.96])
                fig.canvas.draw_idle()

            except (OSError, csv.Error, ValueError) as error:
                print(f"Napaka pri osveževanju grafa: {error}")

        # Prvi prikaz se izriše takoj.
        update(0)

        # Nato se graf osvežuje vsake 3 sekunde.
        ani = FuncAnimation(
            fig,
            update,
            interval=REFRESH_INTERVAL,
            cache_frame_data=False
        )

        # Ohranimo referenco do animacije, da se ne ustavi.
        fig._live_animation = ani

        print("\nGraf se osvežuje vsake 3 sekunde.")
        print("Za zaprtje grafa zapri njegovo okno.")

        plt.show()

    except (OSError, ValueError) as error:
        print(f"\nNapaka: {error}")

    except KeyboardInterrupt:
        print("\nProgram je ustavljen.")


if __name__ == "__main__":
    main()
