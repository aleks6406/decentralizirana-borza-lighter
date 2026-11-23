"""Osnovni testi validacije brez klicev na pravi API."""

import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch


markets_module = importlib.import_module("02_list_markets")
orderbook_module = importlib.import_module("03_get_orderbook")
spread_module = importlib.import_module("04_calculate_spread")
orders_module = importlib.import_module("orders")
currency_module = importlib.import_module("06_currency_conversion")
plot_module = importlib.import_module("07_plot_history")


def make_order(price="10", quantity="2"):
    return {
        "price": price,
        "remaining_base_amount": quantity,
    }


class CalculateSpreadTests(unittest.TestCase):
    def test_valid_orders_find_best_prices_in_any_order(self):
        asks = [make_order("12"), make_order("10")]
        bids = [make_order("8"), make_order("9")]

        result = spread_module.calculate_spread(asks, bids)

        self.assertEqual(result["best_ask"], 10)
        self.assertEqual(result["best_bid"], 9)

    def test_empty_side_is_rejected(self):
        for asks, bids in (([], [make_order()]), ([make_order()], []), ([], [])):
            with self.subTest(asks=asks, bids=bids):
                with self.assertRaisesRegex(ValueError, "potrebujemo"):
                    spread_module.calculate_spread(asks, bids)

    def test_missing_fields_and_wrong_types_are_rejected(self):
        invalid_orders = [
            {"price": "10"},
            make_order(price=[]),
            "not an order",
        ]

        for order in invalid_orders:
            with self.subTest(order=order):
                with self.assertRaises(ValueError):
                    spread_module.calculate_spread([order], [make_order("9")])

        with self.assertRaisesRegex(ValueError, "mora biti seznam"):
            spread_module.calculate_spread({}, [make_order("9")])

    def test_non_positive_and_non_finite_values_are_rejected(self):
        invalid_values = ["0", "-1", "NaN", "Infinity", "-Infinity"]

        for value in invalid_values:
            for field in ("price", "remaining_base_amount"):
                order = make_order()
                order[field] = value
                with self.subTest(value=value, field=field):
                    with self.assertRaises(ValueError):
                        spread_module.calculate_spread([order], [make_order("9")])

    def test_crossed_order_book_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Prekrižan order book"):
            spread_module.calculate_spread([make_order("9")], [make_order("10")])


class ApiValidationTests(unittest.TestCase):
    def test_orderbook_validates_sides_and_keeps_empty_lists(self):
        response = Mock()
        response.json.return_value = {"asks": [make_order()], "bids": []}

        with patch.object(orderbook_module.requests, "get", return_value=response):
            result = orderbook_module.get_orderbook(1)

        self.assertEqual(result["asks"], [make_order()])
        self.assertEqual(result["bids"], [])

    def test_orderbook_rejects_missing_fields_wrong_types_and_bad_values(self):
        invalid_responses = [
            {"asks": []},
            {"bids": []},
            {"asks": {}, "bids": []},
            {"asks": [make_order("NaN")], "bids": []},
            {"asks": [], "bids": [make_order(quantity="0")]},
        ]

        for data in invalid_responses:
            response = Mock()
            response.json.return_value = data
            with patch.object(orderbook_module.requests, "get", return_value=response):
                with self.subTest(data=data):
                    with self.assertRaisesRegex(RuntimeError, "Odgovor API-ja ni veljaven"):
                        orderbook_module.get_orderbook(1)

        response = Mock()
        response.json.return_value = []
        with patch.object(orderbook_module.requests, "get", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "Odgovor API-ja ni veljaven"):
                orderbook_module.get_orderbook(1)

    def test_market_list_checks_response_and_market_fields(self):
        invalid_responses = [
            [],
            {},
            {"order_books": {}},
            {"order_books": [{"symbol": "BTC"}]},
            {"order_books": [{"market_id": "1", "symbol": "BTC"}]},
            {"order_books": [{"market_id": 1, "symbol": " "}]},
        ]

        for data in invalid_responses:
            response = Mock()
            response.json.return_value = data
            with patch.object(markets_module.requests, "get", return_value=response):
                with self.subTest(data=data):
                    with self.assertRaises(RuntimeError):
                        markets_module.get_markets()

        response = Mock()
        response.json.return_value = {
            "order_books": [{"market_id": 1, "symbol": "BTC"}]
        }
        with patch.object(markets_module.requests, "get", return_value=response):
            self.assertEqual(markets_module.get_markets()[0]["symbol"], "BTC")

        response.json.return_value = {
            "order_books": [{"market_id": 0, "symbol": "ETH"}]
        }
        with patch.object(markets_module.requests, "get", return_value=response):
            self.assertEqual(markets_module.get_markets()[0]["market_id"], 0)

    def test_quote_currency_comes_from_asset_metadata(self):
        response = Mock()
        response.json.return_value = {
            "asset_details": [{"asset_id": 3, "symbol": "USD"}]
        }
        with patch.object(markets_module.requests, "get", return_value=response):
            currency = markets_module.get_quote_currency({"quote_asset_id": 3})
        self.assertEqual(currency, "USD")


class OrderUnitTests(unittest.TestCase):
    def test_testnet_markets_uses_testnet_api(self):
        response = Mock()
        response.json.return_value = {"order_books": []}
        with patch.object(orders_module.requests, "get", return_value=response) as get:
            self.assertEqual(orders_module.get_testnet_markets(), [])
        self.assertIn("api.testnet.lighter.xyz", get.call_args.args[0])

    def test_amount_and_price_are_converted_without_rounding(self):
        self.assertEqual(orders_module.to_order_units("0.125", 3), 125)

    def test_invalid_or_too_precise_order_values_are_rejected(self):
        for value in ("0", "-1", "NaN", "Infinity", "abc", "0.001"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    orders_module.to_order_units(value, 2)


class OrderFlowTests(unittest.TestCase):
    def test_declining_order_confirmation_does_not_create_sdk_client(self):
        market = {
            "market_id": 1,
            "symbol": "BTC",
            "status": "active",
            "supported_size_decimals": 2,
            "supported_price_decimals": 1,
            "min_base_amount": "0.01",
        }

        with patch.object(orders_module, "get_testnet_markets", return_value=[market]), \
                patch.object(orders_module, "_create_client") as create_client, \
                patch("builtins.input", side_effect=["1", "buy", "0.10", "10.0", "no"]), \
                patch("builtins.print"):
            orders_module.submit_testnet_order()

        create_client.assert_not_called()

    def test_status_uses_authenticated_account_query(self):
        order = SimpleNamespace(
            status="open", market_index=1, order_index=55,
            remaining_base_amount="0.1",
        )
        client = Mock()
        client.order_api.account_orders = AsyncMock(
            return_value=SimpleNamespace(orders=[order])
        )
        client.close = AsyncMock()

        with patch.object(orders_module, "_create_client", return_value=(client, 7, 4)), \
                patch.object(orders_module, "_get_auth", return_value="test-token"), \
                patch("builtins.input", return_value="123"), \
                patch("builtins.print"):
            orders_module.check_order_status()

        client.order_api.account_orders.assert_awaited_once_with(
            authorization="test-token",
            client_order_indexes="123",
            account_index=7,
        )
        client.close.assert_awaited_once()

    def test_cancel_requires_confirmation_and_closes_client(self):
        order = SimpleNamespace(market_index=1, order_index=55)
        client = Mock()
        client.order_api.account_orders = AsyncMock(
            return_value=SimpleNamespace(orders=[order])
        )
        client.order_api.account_active_orders = AsyncMock(
            return_value=SimpleNamespace(orders=[SimpleNamespace(client_order_index=123)])
        )
        client.cancel_order = AsyncMock()
        client.close = AsyncMock()

        with patch.object(orders_module, "_create_client", return_value=(client, 7, 4)), \
                patch.object(orders_module, "_get_auth", return_value="test-token"), \
                patch("builtins.input", side_effect=["123", "ne"]), \
                patch("builtins.print"):
            orders_module.cancel_open_order()

        client.cancel_order.assert_not_awaited()
        client.close.assert_awaited_once()


class CurrencyRateTests(unittest.TestCase):
    def test_invalid_usd_eur_rates_are_rejected(self):
        for value in ("0", "-1", "NaN", "Infinity", "bad"):
            response = Mock()
            response.json.return_value = {
                "result": "success",
                "rates": {"EUR": value},
            }
            currency_module._cached_rate = None
            currency_module._last_update = 0

            with patch.object(currency_module.requests, "get", return_value=response):
                with self.subTest(value=value):
                    with self.assertRaises(RuntimeError):
                        currency_module.get_usd_to_eur_rate()


class PriceHistoryTests(unittest.TestCase):
    def test_prepare_data_sorts_rows_and_skips_invalid_values(self):
        rows = [
            {
                "market_id": "1", "timestamp": "2026-01-02T00:00:00+00:00",
                "best_bid_eur": "9", "best_ask_eur": "11",
                "spread_eur": "2", "spread_percent": "20",
            },
            {
                "market_id": "1", "timestamp": "2026-01-01T00:00:00+00:00",
                "best_bid_eur": "8", "best_ask_eur": "10",
                "spread_eur": "2", "spread_percent": "25",
            },
            {
                "market_id": "1", "timestamp": "2026-01-03T00:00:00+00:00",
                "best_bid_eur": "NaN", "best_ask_eur": "12",
                "spread_eur": "2", "spread_percent": "10",
            },
        ]

        result = plot_module.prepare_data(rows, "1")

        self.assertEqual(list(result[1]), [8.0, 9.0])
        self.assertEqual(list(result[2]), [10.0, 11.0])

    def test_prepare_data_returns_none_when_no_rows_are_valid(self):
        rows = [{
            "market_id": "1", "timestamp": "not a date",
            "best_bid_eur": "8", "best_ask_eur": "10",
            "spread_eur": "2", "spread_percent": "25",
        }]

        self.assertIsNone(plot_module.prepare_data(rows, "1"))


if __name__ == "__main__":
    unittest.main()
