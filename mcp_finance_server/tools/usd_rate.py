import os

import requests
from dotenv import load_dotenv

load_dotenv()

NAVASAN_API_KEY = os.getenv("NAVASAN_API_KEY")

def get_usd_rate() -> dict:
    """
    Returns the latest US dollar to Toman exchange rate from navasan.tech.

    Returns:
        dict: {"usd_sell_toman": float, "last_update": str}
    """

    if not NAVASAN_API_KEY:
        raise RuntimeError(
            "The navasan API key has not been set. "
            "Set the NAVASAN_API_KEY value in the .env file."
        )


    url = f"https://api.navasan.tech/latest/?api_key={NAVASAN_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        usd_info = data["usd"]

        return {
            "usd_sell_toman": float(usd_info["value"]),
            "last_update": usd_info["date"],
        }

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Retrieving the dollar exchange rate failed: {exc}"
        ) from exc

    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            "The API response structure for navasan is invalid;"
            "Review the received response."
        ) from exc
