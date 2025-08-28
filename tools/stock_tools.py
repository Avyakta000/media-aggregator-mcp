"""Stock Market Tools for FinanceMCP

This module provides tools for fetching stock market data including prices,
quotes, historical data, and fundamental information.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
import yfinance as yf
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import settings

logger = logging.getLogger(__name__)


class StockDataError(Exception):
    """Custom exception for stock data errors."""
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_yahoo_data(symbol: str, period: str = "1d") -> Dict[str, Any]:
    """Fetch data from Yahoo Finance with retry logic."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period=period)
        
        if hist.empty:
            raise StockDataError(f"No data found for symbol: {symbol}")
            
        return {
            "info": info,
            "history": hist.to_dict('records') if not hist.empty else []
        }
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
        raise StockDataError(f"Failed to fetch data for {symbol}: {str(e)}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_alpha_vantage_data(symbol: str, function: str = "TIME_SERIES_DAILY") -> Dict[str, Any]:
    """Fetch data from Alpha Vantage with retry logic."""
    if not settings.alpha_vantage_api_key:
        raise StockDataError("Alpha Vantage API key not configured")
    
    try:
        ts = TimeSeries(key=settings.alpha_vantage_api_key, output_format='pandas')
        
        if function == "TIME_SERIES_DAILY":
            data, meta_data = ts.get_daily(symbol=symbol, outputsize='compact')
        elif function == "TIME_SERIES_INTRADAY":
            data, meta_data = ts.get_intraday(symbol=symbol, interval='1min', outputsize='compact')
        else:
            raise StockDataError(f"Unsupported Alpha Vantage function: {function}")
            
        return {
            "data": data.to_dict('records') if not data.empty else [],
            "meta_data": meta_data
        }
    except Exception as e:
        logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
        raise StockDataError(f"Failed to fetch Alpha Vantage data for {symbol}: {str(e)}")


async def get_stock_price(
    symbol: str,
    source: Literal["yahoo", "alpha_vantage"] = "yahoo"
) -> Dict[str, Any]:
    """
    Get current stock price for a given symbol.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
        source: Data source ("yahoo" or "alpha_vantage")
    
    Returns:
        Dictionary containing current price and basic information
        
    Example:
        >>> await get_stock_price("AAPL")
        {
            "symbol": "AAPL",
            "price": 150.25,
            "change": 2.15,
            "change_percent": 1.45,
            "volume": 1234567,
            "market_cap": 2500000000000,
            "timestamp": "2024-01-15T16:00:00Z"
        }
    """
    try:
        if source == "yahoo":
            data = await _fetch_yahoo_data(symbol, period="1d")
            info = data["info"]
            hist = data["history"]
            
            if not hist:
                raise StockDataError(f"No price data available for {symbol}")
                
            latest = hist[-1] if isinstance(hist, list) else hist.iloc[-1]
            
            return {
                "symbol": symbol,
                "price": float(latest.get("Close", 0)),
                "change": float(latest.get("Close", 0) - latest.get("Open", 0)),
                "change_percent": float(((latest.get("Close", 0) - latest.get("Open", 0)) / latest.get("Open", 1)) * 100),
                "volume": int(latest.get("Volume", 0)),
                "market_cap": info.get("marketCap", 0),
                "timestamp": datetime.now().isoformat() + "Z",
                "source": "yahoo"
            }
        elif source == "alpha_vantage":
            data = await _fetch_alpha_vantage_data(symbol, "TIME_SERIES_DAILY")
            time_series = data["data"]
            
            if not time_series:
                raise StockDataError(f"No price data available for {symbol}")
                
            # Get latest data point
            latest_date = max(time_series.keys())
            latest_data = time_series[latest_date]
            
            return {
                "symbol": symbol,
                "price": float(latest_data["4. close"]),
                "change": float(latest_data["4. close"]) - float(latest_data["1. open"]),
                "change_percent": float(((float(latest_data["4. close"]) - float(latest_data["1. open"])) / float(latest_data["1. open"])) * 100),
                "volume": int(latest_data["5. volume"]),
                "timestamp": latest_date,
                "source": "alpha_vantage"
            }
        else:
            raise StockDataError(f"Unsupported source: {source}")
            
    except Exception as e:
        logger.error(f"Error in get_stock_price for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


async def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive stock quote information.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
    
    Returns:
        Dictionary containing detailed quote information
        
    Example:
        >>> await get_stock_quote("AAPL")
        {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "current_price": 150.25,
            "previous_close": 148.10,
            "open": 149.50,
            "day_high": 151.00,
            "day_low": 148.75,
            "volume": 1234567,
            "market_cap": 2500000000000,
            "pe_ratio": 25.5,
            "dividend_yield": 0.65,
            "sector": "Technology",
            "industry": "Consumer Electronics"
        }
    """
    try:
        data = await _fetch_yahoo_data(symbol, period="5d")
        info = data["info"]
        hist = data["history"]
        
        if not hist:
            raise StockDataError(f"No quote data available for {symbol}")
            
        latest = hist[-1] if isinstance(hist, list) else hist.iloc[-1]
        previous = hist[-2] if len(hist) > 1 else latest
        
        return {
            "symbol": symbol,
            "company_name": info.get("longName", info.get("shortName", symbol)),
            "current_price": float(latest.get("Close", 0)),
            "previous_close": float(previous.get("Close", 0)),
            "open": float(latest.get("Open", 0)),
            "day_high": float(latest.get("High", 0)),
            "day_low": float(latest.get("Low", 0)),
            "volume": int(latest.get("Volume", 0)),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "dividend_yield": info.get("dividendYield", 0),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_stock_quote for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


async def get_stock_history(
    symbol: str,
    period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = "1mo",
    interval: Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"] = "1d"
) -> Dict[str, Any]:
    """
    Get historical stock data.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
        period: Time period for historical data
        interval: Data interval
    
    Returns:
        Dictionary containing historical price data
        
    Example:
        >>> await get_stock_history("AAPL", period="1mo", interval="1d")
        {
            "symbol": "AAPL",
            "period": "1mo",
            "interval": "1d",
            "data": [
                {
                    "date": "2024-01-15",
                    "open": 149.50,
                    "high": 151.00,
                    "low": 148.75,
                    "close": 150.25,
                    "volume": 1234567
                },
                ...
            ]
        }
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise StockDataError(f"No historical data available for {symbol}")
            
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
            
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": data,
            "count": len(data)
        }
        
    except Exception as e:
        logger.error(f"Error in get_stock_history for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


async def get_stock_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Get fundamental financial data for a stock.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
    
    Returns:
        Dictionary containing fundamental data
        
    Example:
        >>> await get_stock_fundamentals("AAPL")
        {
            "symbol": "AAPL",
            "financial_metrics": {
                "market_cap": 2500000000000,
                "enterprise_value": 2600000000000,
                "pe_ratio": 25.5,
                "forward_pe": 24.2,
                "price_to_book": 15.2,
                "debt_to_equity": 0.15,
                "current_ratio": 1.8,
                "return_on_equity": 0.25
            },
            "dividend_info": {
                "dividend_yield": 0.65,
                "dividend_rate": 0.92,
                "payout_ratio": 0.16
            }
        }
    """
    try:
        data = await _fetch_yahoo_data(symbol, period="1d")
        info = data["info"]
        
        return {
            "symbol": symbol,
            "financial_metrics": {
                "market_cap": info.get("marketCap", 0),
                "enterprise_value": info.get("enterpriseValue", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "price_to_book": info.get("priceToBook", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "current_ratio": info.get("currentRatio", 0),
                "return_on_equity": info.get("returnOnEquity", 0),
                "return_on_assets": info.get("returnOnAssets", 0),
                "profit_margins": info.get("profitMargins", 0),
                "operating_margins": info.get("operatingMargins", 0)
            },
            "dividend_info": {
                "dividend_yield": info.get("dividendYield", 0),
                "dividend_rate": info.get("dividendRate", 0),
                "payout_ratio": info.get("payoutRatio", 0)
            },
            "growth_metrics": {
                "revenue_growth": info.get("revenueGrowth", 0),
                "earnings_growth": info.get("earningsGrowth", 0),
                "revenue_per_share": info.get("revenuePerShare", 0),
                "book_value": info.get("bookValue", 0)
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_stock_fundamentals for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


async def search_stocks(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for stocks by company name or symbol.
    
    Args:
        query: Search query (company name or symbol)
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results
        
    Example:
        >>> await search_stocks("Apple", limit=5)
        {
            "query": "Apple",
            "results": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "exchange": "NASDAQ",
                    "type": "Common Stock"
                },
                ...
            ]
        }
    """
    try:
        # Use Yahoo Finance search
        search_results = yf.Tickers(query)
        
        results = []
        count = 0
        
        for ticker in search_results.tickers:
            if count >= limit:
                break
                
            try:
                info = ticker.info
                if info.get("regularMarketPrice"):
                    results.append({
                        "symbol": info.get("symbol", ""),
                        "name": info.get("longName", info.get("shortName", "")),
                        "exchange": info.get("exchange", ""),
                        "type": info.get("quoteType", ""),
                        "market_cap": info.get("marketCap", 0),
                        "current_price": info.get("regularMarketPrice", 0)
                    })
                    count += 1
            except Exception as e:
                logger.warning(f"Error processing ticker {ticker}: {e}")
                continue
                
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in search_stocks for query '{query}': {e}")
        return {"error": str(e), "query": query}
