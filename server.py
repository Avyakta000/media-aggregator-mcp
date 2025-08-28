"""FinanceMCP Server

A production-ready MCP server for financial data using FastMCP.
Provides comprehensive financial data tools including stocks, forex, crypto, and macroeconomic indicators.
"""

import logging
import contextlib
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.server.auth.providers.workos import AuthKitProvider
from starlette.applications import Starlette
from starlette.routing import Mount

# Import all financial tools
from tools.stock_tools import (
    get_stock_price,
    get_stock_quote,
    get_stock_history,
    get_stock_fundamentals,
    search_stocks
)
from tools.forex_tools import (
    get_forex_rate,
    get_forex_history,
    get_currency_list,
    get_currency_converter
)
from tools.crypto_tools import (
    get_crypto_price,
    get_crypto_history,
    get_crypto_list,
    get_crypto_market_data,
    search_cryptocurrencies
)
from tools.macro_tools import (
    get_economic_indicator,
    get_fed_rates,
    get_inflation_data,
    get_gdp_data,
    get_unemployment_data,
    get_popular_indicators
)

from settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("FinanceMCP")

# Initialize MCPAuth (keeping existing integration)
# auth = AuthKitProvider(
#     authkit_domain=settings.authkit_domain,
#     base_url=settings.base_url
# )

# Initialize FastMCP server
mcp = FastMCP(settings.mcp_server_name)

# ==================== STOCK MARKET TOOLS ====================

@mcp.tool()
async def get_stock_price_tool(
    symbol: str,
    source: Literal["yahoo", "alpha_vantage"] = "yahoo"
) -> Dict[str, Any]:
    """
    Fetch real-time stock data using Yahoo Finance.

    Usage:
    - For US stocks: use ticker symbols directly (e.g., "AAPL", "MSFT").
    - For Indian stocks: always include the exchange suffix:    
        - NSE India → ".NS" (e.g., "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS")
        - BSE India → ".BO" (e.g., "RELIANCE.BO", "TCS.BO")

    Examples:
        get_stock_price("AAPL")        # Apple Inc (NASDAQ)
        get_stock_price("RELIANCE.NS") # Reliance Industries (NSE India)
        get_stock_price("PNB.BO")      # Punjab National Bank (BSE India)

    Note:
    If no exchange suffix is provided, the tool may not return the correct stock.
    """

    return await get_stock_price(symbol, source)


@mcp.tool()
async def get_stock_quote_tool(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive stock quote information.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT", "GOOGL")
    
    Returns:
        Dictionary containing detailed quote information
    """
    return await get_stock_quote(symbol)


@mcp.tool()
async def get_stock_history_tool(
    symbol: str,
    period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = "1mo",
    interval: Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"] = "1d"
) -> Dict[str, Any]:
    """
    Get historical stock data.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT", "GOOGL")
        period: Time period for historical data
        interval: Data interval
    
    Returns:
        Dictionary containing historical price data
    """
    return await get_stock_history(symbol, period, interval)


@mcp.tool()
async def get_stock_fundamentals_tool(symbol: str) -> Dict[str, Any]:
    """
    Get fundamental financial data for a stock.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT", "GOOGL")
    
    Returns:
        Dictionary containing fundamental data
    """
    return await get_stock_fundamentals(symbol)


@mcp.tool()
async def search_stocks_tool(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for stocks by company name or symbol.
    
    Args:
        query: Search query (company name or symbol)
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results
    """
    return await search_stocks(query, limit)

# ==================== FOREX TOOLS ====================

@mcp.tool()
async def get_forex_rate_tool(
    from_currency: str,
    to_currency: str,
    source: Literal["yahoo", "alpha_vantage"] = "yahoo"
) -> Dict[str, Any]:
    """
    Get current exchange rate between two currencies.
    
    Args:
        from_currency: Base currency code (e.g., "USD", "EUR", "GBP")
        to_currency: Quote currency code (e.g., "EUR", "USD", "JPY")
        source: Data source ("yahoo" or "alpha_vantage")
    
    Returns:
        Dictionary containing current exchange rate and information
    """
    return await get_forex_rate(from_currency, to_currency, source)


@mcp.tool()
async def get_forex_history_tool(
    from_currency: str,
    to_currency: str,
    period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = "1mo",
    interval: Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"] = "1d"
) -> Dict[str, Any]:
    """
    Get historical forex data.
    
    Args:
        from_currency: Base currency code (e.g., "USD", "EUR", "GBP")
        to_currency: Quote currency code (e.g., "EUR", "USD", "JPY")
        period: Time period for historical data
        interval: Data interval
    
    Returns:
        Dictionary containing historical forex data
    """
    return await get_forex_history(from_currency, to_currency, period, interval)


@mcp.tool()
async def get_currency_list_tool() -> Dict[str, Any]:
    """
    Get list of supported currencies with their information.
    
    Returns:
        Dictionary containing currency list and information
    """
    return await get_currency_list()


@mcp.tool()
async def get_currency_converter_tool(
    amount: float,
    from_currency: str,
    to_currency: str,
    source: Literal["yahoo", "alpha_vantage"] = "yahoo"
) -> Dict[str, Any]:
    """
    Convert amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        source: Data source ("yahoo" or "alpha_vantage")
    
    Returns:
        Dictionary containing conversion result
    """
    return await get_currency_converter(amount, from_currency, to_currency, source)

# ==================== CRYPTOCURRENCY TOOLS ====================

@mcp.tool()
async def get_crypto_price_tool(
    symbol: str,
    market: str = "USD",
    source: Literal["yahoo", "alpha_vantage"] = "yahoo"
) -> Dict[str, Any]:
    """
    Get current cryptocurrency price.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH", "ADA")
        market: Quote currency (e.g., "USD", "EUR", "GBP")
        source: Data source ("yahoo" or "alpha_vantage")
    
    Returns:
        Dictionary containing current price and basic information
    """
    return await get_crypto_price(symbol, market, source)


@mcp.tool()
async def get_crypto_history_tool(
    symbol: str,
    market: str = "USD",
    period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = "1mo",
    interval: Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"] = "1d"
) -> Dict[str, Any]:
    """
    Get historical cryptocurrency data.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH", "ADA")
        market: Quote currency (e.g., "USD", "EUR", "GBP")
        period: Time period for historical data
        interval: Data interval
    
    Returns:
        Dictionary containing historical crypto data
    """
    return await get_crypto_history(symbol, market, period, interval)


@mcp.tool()
async def get_crypto_list_tool() -> Dict[str, Any]:
    """
    Get list of major cryptocurrencies with their information.
    
    Returns:
        Dictionary containing cryptocurrency list and information
    """
    return await get_crypto_list()


@mcp.tool()
async def get_crypto_market_data_tool(symbol: str, market: str = "USD") -> Dict[str, Any]:
    """
    Get comprehensive cryptocurrency market data.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH", "ADA")
        market: Quote currency (e.g., "USD", "EUR", "GBP")
    
    Returns:
        Dictionary containing comprehensive market data
    """
    return await get_crypto_market_data(symbol, market)


@mcp.tool()
async def search_cryptocurrencies_tool(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for cryptocurrencies by name or symbol.
    
    Args:
        query: Search query (cryptocurrency name or symbol)
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results
    """
    return await search_cryptocurrencies(query, limit)

# ==================== MACROECONOMIC TOOLS ====================

@mcp.tool()
async def get_economic_indicator_tool(
    series_id: str,
    observation_start: Optional[str] = None,
    observation_end: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get economic indicator data from FRED.
    
    Args:
        series_id: FRED series ID (e.g., "GDP", "UNRATE", "CPIAUCSL")
        observation_start: Start date (YYYY-MM-DD format)
        observation_end: End date (YYYY-MM-DD format)
    
    Returns:
        Dictionary containing economic indicator data
    """
    return await get_economic_indicator(series_id, observation_start, observation_end)


@mcp.tool()
async def get_fed_rates_tool() -> Dict[str, Any]:
    """
    Get Federal Reserve interest rates.
    
    Returns:
        Dictionary containing Federal Reserve rates data
    """
    return await get_fed_rates()


@mcp.tool()
async def get_inflation_data_tool() -> Dict[str, Any]:
    """
    Get inflation data including CPI and PCE.
    
    Returns:
        Dictionary containing inflation data
    """
    return await get_inflation_data()


@mcp.tool()
async def get_gdp_data_tool() -> Dict[str, Any]:
    """
    Get GDP data including real and nominal GDP.
    
    Returns:
        Dictionary containing GDP data
    """
    return await get_gdp_data()


@mcp.tool()
async def get_unemployment_data_tool() -> Dict[str, Any]:
    """
    Get unemployment data including unemployment rate and labor force participation.
    
    Returns:
        Dictionary containing unemployment data
    """
    return await get_unemployment_data()


@mcp.tool()
async def get_popular_indicators_tool() -> Dict[str, Any]:
    """
    Get list of popular economic indicators with their FRED series IDs.
    
    Returns:
        Dictionary containing popular indicators list
    """
    return await get_popular_indicators()

# ==================== RESOURCES ====================

@mcp.resource("finance://status", mime_type="application/json")
def status_resource() -> Dict[str, Any]:
    """Get FinanceMCP server status."""
    return {
        "name": settings.mcp_server_name,
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat() + "Z"
    }


@mcp.resource("finance://currencies", mime_type="application/json")
async def currencies_resource() -> Dict[str, Any]:
    """Get list of supported currencies."""
    return await get_currency_list()


@mcp.resource("finance://cryptocurrencies", mime_type="application/json")
async def cryptocurrencies_resource() -> Dict[str, Any]:
    """Get list of supported cryptocurrencies."""
    return await get_crypto_list()


@mcp.resource("finance://indicators", mime_type="application/json")
async def indicators_resource() -> Dict[str, Any]:
    """Get list of popular economic indicators."""
    return await get_popular_indicators()


@mcp.resource("finance://stock/{symbol}", mime_type="application/json")
async def stock_resource(symbol: str) -> Dict[str, Any]:
    """Get stock quote for a given symbol."""
    return await get_stock_quote(symbol)


@mcp.resource("finance://forex/{from_currency}/{to_currency}", mime_type="application/json")
async def forex_resource(from_currency: str, to_currency: str) -> Dict[str, Any]:
    """Get forex rate for a given currency pair."""
    return await get_forex_rate(from_currency, to_currency)


@mcp.resource("finance://crypto/{symbol}", mime_type="application/json")
async def crypto_resource(symbol: str, market: str = "USD") -> Dict[str, Any]:
    """Get cryptocurrency price for a given symbol."""
    return await get_crypto_price(symbol, market)


@mcp.resource("finance://macro/fed-rates", mime_type="application/json")
async def fed_rates_resource() -> Dict[str, Any]:
    """Get Federal Reserve rates."""
    return await get_fed_rates()


@mcp.resource("finance://macro/inflation", mime_type="application/json")
async def inflation_resource() -> Dict[str, Any]:
    """Get inflation data."""
    return await get_inflation_data()


@mcp.resource("finance://macro/gdp", mime_type="application/json")
async def gdp_resource() -> Dict[str, Any]:
    """Get GDP data."""
    return await get_gdp_data()

# ==================== PROMPTS ====================

@mcp.prompt
def analyze_stock_market(symbol: str) -> str:
    """Generate a prompt for analyzing a stock's market performance."""
    return f"Analyze the current market performance of {symbol}. Include price trends, volume analysis, and key financial metrics."


@mcp.prompt
def compare_currencies(from_currency: str, to_currency: str) -> str:
    """Generate a prompt for comparing currency performance."""
    return f"Compare the performance of {from_currency} against {to_currency}. Include exchange rate trends and economic factors affecting the currencies."


@mcp.prompt
def crypto_market_analysis(symbol: str) -> str:
    """Generate a prompt for analyzing cryptocurrency market data."""
    return f"Analyze the current market data for {symbol}. Include price trends, market cap, volume, and key metrics."


@mcp.prompt
def economic_outlook() -> str:
    """Generate a prompt for analyzing the current economic outlook."""
    return "Provide a comprehensive analysis of the current economic outlook based on key indicators including GDP, inflation, unemployment, and Federal Reserve rates."


@mcp.prompt
def investment_recommendation(asset_type: str, symbol: str) -> str:
    """Generate a prompt for investment recommendations."""
    return f"Provide an investment analysis and recommendation for {symbol} ({asset_type}). Include risk assessment, market conditions, and key factors to consider."

# ==================== SERVER SETUP ====================

# Create HTTP app
mcp_app = mcp.http_app(path='/mcp')

# Create Starlette app with MCP integration
app = Starlette(
    routes=[
        Mount("/", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan,
)

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.mcp_server_name} server...")
    logger.info("Available tools:")
    logger.info("- Stock Market: get_stock_price, get_stock_quote, get_stock_history, get_stock_fundamentals, search_stocks")
    logger.info("- Forex: get_forex_rate, get_forex_history, get_currency_list, get_currency_converter")
    logger.info("- Cryptocurrency: get_crypto_price, get_crypto_history, get_crypto_list, get_crypto_market_data, search_cryptocurrencies")
    logger.info("- Macroeconomic: get_economic_indicator, get_fed_rates, get_inflation_data, get_gdp_data, get_unemployment_data, get_popular_indicators")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
