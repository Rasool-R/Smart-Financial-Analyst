import pytse_client as tse
from datetime import datetime

def get_stock_info(symbol: str) -> dict:
    """
    Retrieves real-time data for an Iranian stock market ticker from TSETMC.

    Args:
        symbol (str): The stock ticker symbol in Persian or English, exactly as registered on TSETMC. Example: "فولاد"

    Returns:
        dict: Dictionary with the following keys:
            - symbol (str): Stock Ticker Symbol
            - name (str): Company name
            - last_price (float): Last Traded Price (Tomans)
            - price_change_percent (float): Percentage change compared to the previous day
            - volume (int): Trading volume
            - market_cap (float | None): Market value, if available
            - last_update (str): Last update time in ISO 8601 format

    Raises:
        ValueError: اگر نماد وارد‌شده در TSETMC یافت نشود.
    """
    try:
        ticker = tse.Ticker(symbol)

        last_price = ticker.last_price
        yesterday_price = ticker.yesterday_price

        if yesterday_price and yesterday_price > 0:
            price_change_percent = round(
                ((last_price - yesterday_price) / yesterday_price) * 100, 2
            )
        else:
            price_change_percent = 0.0

        return {
            "symbol": symbol,
            "name": ticker.title,
            "last_price": last_price,
            "price_change_percent": price_change_percent,
            "volume": int(ticker.volume),
            "cap_market": None,
            "last_update": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise ValueError(
            f"{symbol} not found: {e}"
        )