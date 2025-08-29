"""FinanceMCP Server

A production-ready MCP server for financial data using FastMCP.
Provides comprehensive financial data tools including Indian stocks and macroeconomic indicators.
"""

import logging
import contextlib
from typing import Any, Dict, List, Optional
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
    search_stocks,
    analyze_stock
)

from tools.macro_tools import (
    get_economic_indicator,
    get_fed_rates,
    get_inflation_data,
    get_gdp_data,
    get_unemployment_data,
    get_popular_indicators
)

from tools.types import DataSource, ApiResponse

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
# Note: analyze_stock_tool provides comprehensive research-style analysis
# while other tools provide specific data points for different use cases

@mcp.tool()
async def get_stock_price_tool(
    symbol: str,
    source: DataSource = "yahoo"
) -> ApiResponse:
    """
    Fetch real-time stock data for Indian markets using Yahoo Finance.
    
    Usage:
    - For Indian stocks: you can pass just the stock name or include the exchange suffix:
        - Just stock name: "RELIANCE", "TCS", "HDFCBANK" (will automatically try NSE first, then BSE)
        - NSE India → ".NS" (e.g., "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS")
        - BSE India → ".BO" (e.g., "RELIANCE.BO", "TCS.BO")
    
    Examples:
        get_stock_price("RELIANCE")     # Will try RELIANCE.NS first, then RELIANCE.BO
        get_stock_price("RELIANCE.NS")  # Uses NSE explicitly
        get_stock_price("TCS.NS")       # Tata Consultancy Services (NSE India)
        get_stock_price("HDFCBANK.NS")  # HDFC Bank (NSE India)
        get_stock_price("PNB.BO")       # Punjab National Bank (BSE India)
    
    Note:
    This tool is configured for Indian markets only. If no exchange suffix is provided, it will automatically try NSE (.NS) first, then BSE (.BO).
    """
    return await get_stock_price(symbol, source)


@mcp.tool()
async def get_stock_quote_tool(symbol: str) -> ApiResponse:
    """
    Get comprehensive stock quote information for Indian stocks.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "PNB.BO")
               If no exchange suffix is provided, will automatically try NSE (.NS) first, then BSE (.BO)
    
    Returns:
        Dictionary containing detailed quote information
    """
    return await get_stock_quote(symbol)


@mcp.tool()
async def get_stock_history_tool(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d"
) -> ApiResponse:
    """
    Get historical stock data for Indian stocks.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "PNB.BO")
               If no exchange suffix is provided, will automatically try NSE (.NS) first, then BSE (.BO)
        period: Time period for historical data
        interval: Data interval
    
    Returns:
        Dictionary containing historical price data
    """
    return await get_stock_history(symbol, period, interval)


@mcp.tool()
async def get_stock_fundamentals_tool(symbol: str) -> ApiResponse:
    """
    Get fundamental financial data for Indian stocks.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "PNB.BO")
               If no exchange suffix is provided, will automatically try NSE (.NS) first, then BSE (.BO)
    
    Returns:
        Dictionary containing fundamental data
    """
    return await get_stock_fundamentals(symbol)


@mcp.tool()
async def search_stocks_tool(query: str, limit: int = 10) -> ApiResponse:
    """
    Search for Indian stocks by company name or symbol.
    
    Args:
        query: Search query (company name or symbol)
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results (prioritizes Indian stocks)
    """
    return await search_stocks(query, limit)


@mcp.tool()
async def analyze_stock_tool(
    symbol: str,
    period: str = "1y",
    interval: str = "1d"
) -> ApiResponse:
    """
    Provide a structured research-style analysis of a stock combining overview, 
    fundamentals, technicals, valuation, and summary.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "PNB.BO")
               If no exchange suffix is provided, will automatically try NSE (.NS) first, then BSE (.BO)
        period: Time period for historical data (default: "1y")
        interval: Data interval (default: "1d")
    
    Returns:
        Dictionary containing comprehensive stock analysis including:
        - Company profile (name, sector, industry, market cap, description)
        - Fundamentals (valuation ratios, profitability, growth, financial health)
        - Technicals (price, moving averages, RSI, MACD, trend signals)
        - Summary (strengths, risks, overall view)
        
    Example:
        >>> analyze_stock_tool("RELIANCE")
        Returns comprehensive analysis of Reliance Industries with all metrics
    """
    return await analyze_stock(symbol, period, interval)

# ==================== MACROECONOMIC TOOLS ====================

@mcp.tool()
async def get_economic_indicator_tool(
    series_id: str,
    observation_start: Optional[str] = None,
    observation_end: Optional[str] = None
) -> ApiResponse:
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
async def get_fed_rates_tool() -> ApiResponse:
    """
    Get Federal Reserve interest rates.
    
    Returns:
        Dictionary containing Federal Reserve rates data
    """
    return await get_fed_rates()


@mcp.tool()
async def get_inflation_data_tool() -> ApiResponse:
    """
    Get inflation data including CPI and PCE.
    
    Returns:
        Dictionary containing inflation data
    """
    return await get_inflation_data()


@mcp.tool()
async def get_gdp_data_tool() -> ApiResponse:
    """
    Get GDP data including real and nominal GDP.
    
    Returns:
        Dictionary containing GDP data
    """
    return await get_gdp_data()


@mcp.tool()
async def get_unemployment_data_tool() -> ApiResponse:
    """
    Get unemployment data including unemployment rate and labor force participation.
    
    Returns:
        Dictionary containing unemployment data
    """
    return await get_unemployment_data()


@mcp.tool()
async def get_popular_indicators_tool() -> ApiResponse:
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


@mcp.resource("finance://indicators", mime_type="application/json")
async def indicators_resource() -> Dict[str, Any]:
    """Get list of popular economic indicators."""
    return await get_popular_indicators()


@mcp.resource("finance://stock/{symbol}", mime_type="application/json")
async def stock_resource(symbol: str) -> Dict[str, Any]:
    """Get stock quote for a given symbol."""
    return await get_stock_quote(symbol)


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
    logger.info("- Indian Stock Market: get_stock_price, get_stock_quote, get_stock_history, get_stock_fundamentals, search_stocks, analyze_stock_tool")
    logger.info("- Macroeconomic: get_economic_indicator, get_fed_rates, get_inflation_data, get_gdp_data, get_unemployment_data, get_popular_indicators")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
