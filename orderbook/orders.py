"""Preprosto pošiljanje in upravljanje naročil na Lighter testnetu."""

import asyncio
import os
import time
from decimal import Decimal, InvalidOperation

import requests


TESTNET_URL = "https://api.testnet.lighter.xyz"


def to_order_units(value, decimals):
    """Pretvori uporabnikov decimalni vnos v celoštevilske enote Lighterja."""

    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError("Vnesi veljavno številko.")

    if not number.is_finite() or number <= 0:
        raise ValueError("Vrednost mora biti končna in večja od nič.")

    scaled = number * (10 ** decimals)
    if scaled != scaled.to_integral_value():
        raise ValueError(f"Trg podpira največ {decimals} decimalnih mest.")

    return int(scaled)


def get_testnet_markets():
    """Pridobi trge iz testnega omrežja, ne iz glavnega omrežja."""

    response = requests.get(f"{TESTNET_URL}/api/v1/orderBooks", timeout=10)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict) or not isinstance(data.get("order_books"), list):
        raise RuntimeError("Testnet ni vrnil veljavnega seznama trgov.")

    return data["order_books"]


def _create_client():
    """Pripravi SDK odjemalca iz okolijskih spremenljivk."""

    api_key = os.getenv("LIGHTER_API_PRIVATE_KEY")
    account_index = os.getenv("LIGHTER_ACCOUNT_INDEX")
    api_key_index = os.getenv("LIGHTER_API_KEY_INDEX")

    if not api_key or not account_index or not api_key_index:
        raise RuntimeError(
            "Nastavi LIGHTER_API_PRIVATE_KEY, LIGHTER_ACCOUNT_INDEX in "
            "LIGHTER_API_KEY_INDEX v lokalni datoteki .env."
        )

    try:
        import lighter
    except ImportError as error:
        raise RuntimeError("Za naročila namesti odvisnosti iz requirements.txt.") from error

    client = lighter.SignerClient(
        url=TESTNET_URL,
        account_index=int(account_index),
        api_private_keys={int(api_key_index): api_key},
        chain_id=300,
    )

    error = client.check_client()
    if error:
        raise RuntimeError(f"Preverjanje API ključa ni uspelo: {error}")

    return client, int(account_index), int(api_key_index)


def _get_auth(client, api_key_index):
    token, error = client.create_auth_token_with_expiry(api_key_index=api_key_index)
    if error:
        raise RuntimeError(f"Ustvarjanje kratkotrajnega dostopa ni uspelo: {error}")
    return token


async def _submit_testnet_order():
    markets = get_testnet_markets()
    print("Trgi na Lighter testnetu:")
    for market in markets:
        if market.get("status") == "active":
            print(market.get("market_id"), market.get("symbol"), market.get("market_type"))

    market_id = int(input("Vnesi testnet market ID: ").strip())
    market = next(
        (item for item in markets if item.get("market_id") == market_id),
        None,
    )
    if market is None or market.get("status") != "active":
        raise ValueError("Izbrani trg ne obstaja ali ni aktiven na testnetu.")

    side = input("Stran (buy/sell): ").strip().lower()
    if side not in ("buy", "sell"):
        raise ValueError("Vnesi buy ali sell.")

    input_amount = input("Količina: ").strip()
    input_price = input("Limitna cena: ").strip()
    amount = to_order_units(input_amount, market["supported_size_decimals"])
    price = to_order_units(input_price, market["supported_price_decimals"])
    minimum = Decimal(str(market.get("min_base_amount", "0")))
    if Decimal(amount) / (10 ** market["supported_size_decimals"]) < minimum:
        raise ValueError(f"Najmanjša količina za trg je {minimum}.")

    client_order_index = int(time.time() * 1000)
    print("\nPovzetek testnega naročila:")
    print("Omrežje: Lighter testnet")
    print("Trg:", market["symbol"], "(ID", market_id, ")")
    print("Stran:", side)
    print("Količina:", input_amount)
    print("Limitna cena:", input_price)
    print("Vrsta: limitno, post-only")
    if input("Za oddajo v testnet vpiši ODDAJ: ").strip() != "ODDAJ":
        print("Naročilo ni bilo oddano.")
        return

    client, _, _ = _create_client()
    try:
        _, response, error = await client.create_order(
            market_index=market_id,
            client_order_index=client_order_index,
            base_amount=amount,
            price=price,
            is_ask=(side == "sell"),
            order_type=client.ORDER_TYPE_LIMIT,
            time_in_force=client.ORDER_TIME_IN_FORCE_POST_ONLY,
            reduce_only=False,
            trigger_price=0,
        )
        if error:
            print("Testnet je zavrnil naročilo:", error)
        else:
            print("Testnet je sprejel zahtevo.")
            print("Client order index:", client_order_index)
            print("Transakcijska koda:", response.code)
    finally:
        await client.close()


def submit_testnet_order():
    asyncio.run(_submit_testnet_order())


async def _check_order_status():
    client_order_index = int(input("Vnesi client order index: ").strip())
    client, account_index, api_key_index = _create_client()
    try:
        token = _get_auth(client, api_key_index)
        result = await client.order_api.account_orders(
            authorization=token,
            client_order_indexes=str(client_order_index),
            account_index=account_index,
        )
        if not result.orders:
            print("Naročila s tem ID-jem ni v odgovoru API-ja.")
            return
        for order in result.orders:
            print("Status:", order.status)
            print("Trg ID:", order.market_index)
            print("ID naročila:", order.order_index)
            print("Preostala količina:", order.remaining_base_amount)
    finally:
        await client.close()


def check_order_status():
    asyncio.run(_check_order_status())


async def _cancel_open_order():
    client_order_index = int(input("Vnesi client order index: ").strip())
    client, account_index, api_key_index = _create_client()
    try:
        token = _get_auth(client, api_key_index)
        result = await client.order_api.account_orders(
            authorization=token,
            client_order_indexes=str(client_order_index),
            account_index=account_index,
        )
        if not result.orders:
            print("Naročila ni mogoče najti.")
            return

        order = result.orders[0]
        active = await client.order_api.account_active_orders(
            authorization=token,
            account_index=account_index,
            market_id=order.market_index,
        )
        open_order = next(
            (item for item in active.orders if item.client_order_index == client_order_index),
            None,
        )
        if open_order is None:
            print("Naročilo ni odprto, zato ga ni mogoče preklicati.")
            return

        print("Prekliči odprto naročilo na trgu", order.market_index, "?")
        if input("Za potrditev vpiši PREKLICI: ").strip() != "PREKLICI":
            print("Preklic ni bil poslan.")
            return

        _, response, error = await client.cancel_order(
            market_index=order.market_index,
            order_index=order.order_index,
        )
        if error:
            print("Preklic ni uspel:", error)
        else:
            print("Zahteva za preklic je poslana. Koda:", response.code)
    finally:
        await client.close()


def cancel_open_order():
    asyncio.run(_cancel_open_order())
