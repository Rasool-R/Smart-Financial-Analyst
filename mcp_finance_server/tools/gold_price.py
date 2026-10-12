import requests

def get_gold_price() -> dict:
    """
    Retrieves the real-time global gold price (per ounce, in USD) from gold-api.com.

    Returns:
        dict: {"symbol": "XAU", "price_usd_per_ounce": float, "name": str}
    """

    url = "https://api.gold-api.com/price/XAU"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "symbol": data["symbol"],
            "price_usd_per_ounce": float(data["price"]),
            "name": data.get("name", "Gold"),
        }

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Retrieving the global gold price was unsuccessful: {exc}"
        ) from exc

    except (ValueError, KeyError) as exc:
        raise RuntimeError(
            "The gold price API response is invalid."
        ) from exc
