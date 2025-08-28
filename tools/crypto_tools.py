"""Cryptocurrency Tools for FinanceMCP

This module provides tools for fetching cryptocurrency data including prices,
historical data, and market information.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
import yfinance as yf
import pandas as pd
from alpha_vantage.cryptocurrencies import CryptoCurrencies
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import settings

logger = logging.getLogger(__name__)


class CryptoDataError(Exception):
    """Custom exception for cryptocurrency data errors."""
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_yahoo_crypto_data(symbol: str, period: str = "1d") -> Dict[str, Any]:
    """Fetch cryptocurrency data from Yahoo Finance with retry logic."""
    try:
        # Yahoo Finance uses format like "BTC-USD" for cryptocurrencies
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period=period)
        
        if hist.empty:
            raise CryptoDataError(f"No crypto data found for {symbol}")
            
        return {
            "info": info,
            "history": hist.to_dict('records') if not hist.empty else []
        }
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance crypto data for {symbol}: {e}")
        raise CryptoDataError(f"Failed to fetch crypto data for {symbol}: {str(e)}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_alpha_vantage_crypto_data(symbol: str, market: str = "USD", function: str = "DIGITAL_CURRENCY_DAILY") -> Dict[str, Any]:
    """Fetch cryptocurrency data from Alpha Vantage with retry logic."""
    if not settings.alpha_vantage_api_key:
        raise CryptoDataError("Alpha Vantage API key not configured")
    
    try:
        cc = CryptoCurrencies(key=settings.alpha_vantage_api_key, output_format='pandas')
        
        if function == "DIGITAL_CURRENCY_DAILY":
            data, meta_data = cc.get_digital_currency_daily(symbol=symbol, market=market)
        elif function == "DIGITAL_CURRENCY_WEEKLY":
            data, meta_data = cc.get_digital_currency_weekly(symbol=symbol, market=market)
        elif function == "DIGITAL_CURRENCY_MONTHLY":
            data, meta_data = cc.get_digital_currency_monthly(symbol=symbol, market=market)
        else:
            raise CryptoDataError(f"Unsupported Alpha Vantage crypto function: {function}")
            
        return {
            "data": data.to_dict('records') if not data.empty else [],
            "meta_data": meta_data
        }
    except Exception as e:
        logger.error(f"Error fetching Alpha Vantage crypto data for {symbol}: {e}")
        raise CryptoDataError(f"Failed to fetch Alpha Vantage crypto data for {symbol}: {str(e)}")


async def get_crypto_price(
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
        
    Example:
        >>> await get_crypto_price("BTC", "USD")
        {
            "symbol": "BTC",
            "market": "USD",
            "price": 45000.50,
            "change": 1250.25,
            "change_percent": 2.86,
            "volume": 25000000000,
            "market_cap": 850000000000,
            "timestamp": "2024-01-15T16:00:00Z"
        }
    """
    try:
        if source == "yahoo":
            # Yahoo Finance format: BTC-USD, ETH-USD, etc.
            yahoo_symbol = f"{symbol}-{market}"
            data = await _fetch_yahoo_crypto_data(yahoo_symbol, period="1d")
            info = data["info"]
            hist = data["history"]
            
            if not hist:
                raise CryptoDataError(f"No crypto data available for {symbol}")
                
            latest = hist[-1] if isinstance(hist, list) else hist.iloc[-1]
            previous = hist[-2] if len(hist) > 1 else latest
            
            return {
                "symbol": symbol,
                "market": market,
                "price": float(latest.get("Close", 0)),
                "change": float(latest.get("Close", 0) - previous.get("Close", 0)),
                "change_percent": float(((latest.get("Close", 0) - previous.get("Close", 0)) / previous.get("Close", 1)) * 100),
                "volume": int(latest.get("Volume", 0)),
                "market_cap": info.get("marketCap", 0),
                "circulating_supply": info.get("circulatingSupply", 0),
                "max_supply": info.get("maxSupply", 0),
                "timestamp": datetime.now().isoformat() + "Z",
                "source": "yahoo"
            }
        elif source == "alpha_vantage":
            data = await _fetch_alpha_vantage_crypto_data(symbol, market, "DIGITAL_CURRENCY_DAILY")
            time_series = data["data"]
            
            if not time_series:
                raise CryptoDataError(f"No crypto data available for {symbol}")
                
            # Get latest data point
            latest_date = max(time_series.keys())
            latest_data = time_series[latest_date]
            
            return {
                "symbol": symbol,
                "market": market,
                "price": float(latest_data[f"4a. close ({market})"]),
                "change": float(latest_data[f"4a. close ({market})"]) - float(latest_data[f"1a. open ({market})"]),
                "change_percent": float(((float(latest_data[f"4a. close ({market})"]) - float(latest_data[f"1a. open ({market})"])) / float(latest_data[f"1a. open ({market})"])) * 100),
                "volume": int(latest_data["5. volume"]),
                "market_cap": float(latest_data[f"6. market cap ({market})"]),
                "timestamp": latest_date,
                "source": "alpha_vantage"
            }
        else:
            raise CryptoDataError(f"Unsupported source: {source}")
            
    except Exception as e:
        logger.error(f"Error in get_crypto_price for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol, "market": market}


async def get_crypto_history(
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
        
    Example:
        >>> await get_crypto_history("BTC", "USD", period="1mo", interval="1d")
        {
            "symbol": "BTC",
            "market": "USD",
            "period": "1mo",
            "interval": "1d",
            "data": [
                {
                    "date": "2024-01-15",
                    "open": 44500.00,
                    "high": 45200.00,
                    "low": 44300.00,
                    "close": 45000.50,
                    "volume": 25000000000
                },
                ...
            ]
        }
    """
    try:
        yahoo_symbol = f"{symbol}-{market}"
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise CryptoDataError(f"No historical crypto data available for {symbol}")
            
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
            "market": market,
            "period": period,
            "interval": interval,
            "data": data,
            "count": len(data)
        }
        
    except Exception as e:
        logger.error(f"Error in get_crypto_history for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol, "market": market}


async def get_crypto_list() -> Dict[str, Any]:
    """
    Get list of major cryptocurrencies with their information.
    
    Returns:
        Dictionary containing cryptocurrency list and information
        
    Example:
        >>> await get_crypto_list()
        {
            "cryptocurrencies": [
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "full_name": "Bitcoin",
                    "type": "cryptocurrency"
                },
                {
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "full_name": "Ethereum",
                    "type": "cryptocurrency"
                },
                ...
            ]
        }
    """
    try:
        # Major cryptocurrencies
        cryptocurrencies = [
            {"symbol": "BTC", "name": "Bitcoin", "full_name": "Bitcoin", "type": "cryptocurrency"},
            {"symbol": "ETH", "name": "Ethereum", "full_name": "Ethereum", "type": "cryptocurrency"},
            {"symbol": "USDT", "name": "Tether", "full_name": "Tether USD", "type": "stablecoin"},
            {"symbol": "BNB", "name": "BNB", "full_name": "Binance Coin", "type": "cryptocurrency"},
            {"symbol": "SOL", "name": "Solana", "full_name": "Solana", "type": "cryptocurrency"},
            {"symbol": "USDC", "name": "USD Coin", "full_name": "USD Coin", "type": "stablecoin"},
            {"symbol": "ADA", "name": "Cardano", "full_name": "Cardano", "type": "cryptocurrency"},
            {"symbol": "AVAX", "name": "Avalanche", "full_name": "Avalanche", "type": "cryptocurrency"},
            {"symbol": "DOGE", "name": "Dogecoin", "full_name": "Dogecoin", "type": "cryptocurrency"},
            {"symbol": "DOT", "name": "Polkadot", "full_name": "Polkadot", "type": "cryptocurrency"},
            {"symbol": "MATIC", "name": "Polygon", "full_name": "Polygon", "type": "cryptocurrency"},
            {"symbol": "LINK", "name": "Chainlink", "full_name": "Chainlink", "type": "cryptocurrency"},
            {"symbol": "UNI", "name": "Uniswap", "full_name": "Uniswap", "type": "cryptocurrency"},
            {"symbol": "LTC", "name": "Litecoin", "full_name": "Litecoin", "type": "cryptocurrency"},
            {"symbol": "BCH", "name": "Bitcoin Cash", "full_name": "Bitcoin Cash", "type": "cryptocurrency"},
            {"symbol": "XLM", "name": "Stellar", "full_name": "Stellar", "type": "cryptocurrency"},
            {"symbol": "ATOM", "name": "Cosmos", "full_name": "Cosmos", "type": "cryptocurrency"},
            {"symbol": "ETC", "name": "Ethereum Classic", "full_name": "Ethereum Classic", "type": "cryptocurrency"},
            {"symbol": "XRP", "name": "XRP", "full_name": "XRP", "type": "cryptocurrency"},
            {"symbol": "FIL", "name": "Filecoin", "full_name": "Filecoin", "type": "cryptocurrency"},
        ]
        
        return {
            "cryptocurrencies": cryptocurrencies,
            "count": len(cryptocurrencies),
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_crypto_list: {e}")
        return {"error": str(e)}


async def get_crypto_market_data(symbol: str, market: str = "USD") -> Dict[str, Any]:
    """
    Get comprehensive cryptocurrency market data.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC", "ETH", "ADA")
        market: Quote currency (e.g., "USD", "EUR", "GBP")
    
    Returns:
        Dictionary containing comprehensive market data
        
    Example:
        >>> await get_crypto_market_data("BTC", "USD")
        {
            "symbol": "BTC",
            "market": "USD",
            "market_data": {
                "current_price": 45000.50,
                "market_cap": 850000000000,
                "market_cap_rank": 1,
                "volume_24h": 25000000000,
                "circulating_supply": 19500000,
                "max_supply": 21000000,
                "total_supply": 19500000
            },
            "price_change": {
                "change_24h": 1250.25,
                "change_percent_24h": 2.86,
                "change_7d": 3500.00,
                "change_percent_7d": 8.43
            }
        }
    """
    try:
        yahoo_symbol = f"{symbol}-{market}"
        data = await _fetch_yahoo_crypto_data(yahoo_symbol, period="7d")
        info = data["info"]
        hist = data["history"]
        
        if not hist:
            raise CryptoDataError(f"No market data available for {symbol}")
            
        latest = hist[-1] if isinstance(hist, list) else hist.iloc[-1]
        day_ago = hist[-2] if len(hist) > 1 else latest
        week_ago = hist[-8] if len(hist) > 7 else latest
        
        return {
            "symbol": symbol,
            "market": market,
            "market_data": {
                "current_price": float(latest.get("Close", 0)),
                "market_cap": info.get("marketCap", 0),
                "market_cap_rank": info.get("marketCapRank", 0),
                "volume_24h": int(latest.get("Volume", 0)),
                "circulating_supply": info.get("circulatingSupply", 0),
                "max_supply": info.get("maxSupply", 0),
                "total_supply": info.get("totalSupply", 0),
                "ath": info.get("fiftyTwoWeekHigh", 0),
                "atl": info.get("fiftyTwoWeekLow", 0)
            },
            "price_change": {
                "change_24h": float(latest.get("Close", 0) - day_ago.get("Close", 0)),
                "change_percent_24h": float(((latest.get("Close", 0) - day_ago.get("Close", 0)) / day_ago.get("Close", 1)) * 100),
                "change_7d": float(latest.get("Close", 0) - week_ago.get("Close", 0)),
                "change_percent_7d": float(((latest.get("Close", 0) - week_ago.get("Close", 0)) / week_ago.get("Close", 1)) * 100)
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_crypto_market_data for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol, "market": market}


async def search_cryptocurrencies(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for cryptocurrencies by name or symbol.
    
    Args:
        query: Search query (cryptocurrency name or symbol)
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results
        
    Example:
        >>> await search_cryptocurrencies("Bitcoin", limit=5)
        {
            "query": "Bitcoin",
            "results": [
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "full_name": "Bitcoin",
                    "current_price": 45000.50,
                    "market_cap": 850000000000
                },
                ...
            ]
        }
    """
    try:
        # Use Yahoo Finance search for crypto
        search_results = yf.Tickers(query)
        
        results = []
        count = 0
        
        for ticker in search_results.tickers:
            if count >= limit:
                break
                
            try:
                info = ticker.info
                if info.get("regularMarketPrice") and info.get("quoteType") == "CRYPTOCURRENCY":
                    results.append({
                        "symbol": info.get("symbol", "").split("-")[0],  # Remove market suffix
                        "name": info.get("shortName", ""),
                        "full_name": info.get("longName", ""),
                        "current_price": info.get("regularMarketPrice", 0),
                        "market_cap": info.get("marketCap", 0),
                        "volume_24h": info.get("volume", 0)
                    })
                    count += 1
            except Exception as e:
                logger.warning(f"Error processing crypto ticker {ticker}: {e}")
                continue
                
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in search_cryptocurrencies for query '{query}': {e}")
        return {"error": str(e), "query": query}
