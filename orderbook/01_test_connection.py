
import requests


def check_connection():
    url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBooks"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    print("Povezava z Lighter API-jem deluje.")


if __name__ == "__main__":
    try:
        check_connection()
    except requests.RequestException as error:
        print("Povezava ni uspela:", error)
