
import requests

url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBooks"
response = requests.get(url, timeout=10)
print("HTTP status:", response.status_code)
