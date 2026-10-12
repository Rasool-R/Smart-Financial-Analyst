from mcp.server.fastmcp import FastMCP

from tools.stock_info import get_stock_info
from tools.gold_price import get_gold_price
from tools.usd_rate import get_usd_rate


mcp = FastMCP("Finance Assistant")


@mcp.tool()
def stock_info(symbol: str) -> dict:
    """
    Retrieving data for an Iranian stock market ticker from TSETMC.

    Args:
        symbol: Stock market ticker symbol, such as فولاد or خودرو.

    Returns:
        Stock information includes price, trading volume, and other specifications.
    """
    return get_stock_info(symbol)


@mcp.tool()
def gold_price() -> dict:
    """
    Get the global price of gold per ounce in US dollars.

    Returns:
        Gold symbol, price per ounce in dollars, and asset name.
    """
    return get_gold_price()


@mcp.tool()
def usd_rate() -> dict:
    """
    Get the latest US dollar to Toman exchange rate.

    Returns:
        Dollar-to-Toman exchange rate and time of last update.
    """
    return get_usd_rate()

if __name__ == "__main__":
    mcp.run(transport="stdio")