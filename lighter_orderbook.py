import requests

# Pridobimo seznam trgov
markets_url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBooks"
markets_response = requests.get(markets_url, timeout=10)
markets_response.raise_for_status()

markets_data = markets_response.json()

market_id = 1

# Poiščemo ime trga glede na market_id
market = next(
    m for m in markets_data["order_books"]
    if m["market_id"] == market_id
)

market_name = market["symbol"]

# Pridobimo naročila za izbrani trg
url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBookOrders"

params = {
    "market_id": market_id,
    "limit": 10
}

response = requests.get(url, params=params, timeout=10)
response.raise_for_status()

data = response.json()

asks = data["asks"]
bids = data["bids"]

best_ask = float(asks[0]["price"])
best_bid = float(bids[0]["price"])

ask_quantity = float(asks[0]["remaining_base_amount"])
bid_quantity = float(bids[0]["remaining_base_amount"])

spread = best_ask - best_bid
spread_percent = (spread / best_bid) * 100

print("Trg:", market_name)
print("Najboljša prodajna cena:", best_ask)
print("Količina za prodajo pri tej ceni:", ask_quantity)
print("Najboljša nakupna cena:", best_bid)
print("Količina za nakup pri tej ceni:", bid_quantity)
print("Spread:", round(spread, 8))
print("Spread v odstotkih:", round(spread_percent, 4), "%")