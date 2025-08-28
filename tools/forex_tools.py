"""Forex (Foreign Exchange) Tools for FinanceMCP

This module provides tools for fetching foreign exchange data including
currency rates, historical data, and currency information.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
import yfinance as yf
import pandas as pd
from alpha_vantage.foreignexchange import ForeignExchange
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import settings

logger = logging.getLogger(__name__)


class ForexDataError(Exception):
    """Custom exception for forex data errors."""
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_yahoo_forex_data(from_currency: str, to_currency: str, period: str = "1d") -> Dict[str, Any]:
    """Fetch forex data from Yahoo Finance with retry logic."""
    try:
        # Yahoo Finance uses format like "EURUSD=X" for forex pairs
        symbol = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period=period)
        
        if hist.empty:
            raise ForexDataError(f"No forex data found for {from_currency}/{to_currency}")
            
        return {
            "info": info,
            "history": hist.to_dict('records') if not hist.empty else []
        }
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance forex data for {from_currency}/{to_currency}: {e}")
        raise ForexDataError(f"Failed to fetch forex data for {from_currency}/{to_currency}: {str(e)}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_alpha_vantage_forex_data(from_currency: str, to_currency: str, function: str = "CURRENCY_EXCHANGE_RATE") -> Dict[str, Any]:
    """Fetch forex data from Alpha Vantage with retry logic."""
    if not settings.alpha_vantage_api_key:
        raise ForexDataError("Alpha Vantage API key not configured")
    
    try:
        fx = ForeignExchange(key=settings.alpha_vantage_api_key)
        
        if function == "CURRENCY_EXCHANGE_RATE":
            data, meta_data = fx.get_currency_exchange_rate(from_currency=from_currency, to_currency=to_currency)
        elif function == "FX_DAILY":
            data, meta_data = fx.get_currency_exchange_daily(from_symbol=from_currency, to_symbol=to_currency, outputsize='compact')
        else:
            raise ForexDataError(f"Unsupported Alpha Vantage forex function: {function}")
            
        return {
            "data": data,
            "meta_data": meta_data
        }
    except Exception as e:
        logger.error(f"Error fetching Alpha Vantage forex data for {from_currency}/{to_currency}: {e}")
        raise ForexDataError(f"Failed to fetch Alpha Vantage forex data for {from_currency}/{to_currency}: {str(e)}")


async def get_forex_rate(
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
        
    Example:
        >>> await get_forex_rate("USD", "EUR")
        {
            "from_currency": "USD",
            "to_currency": "EUR",
            "rate": 0.85,
            "inverse_rate": 1.18,
            "change": 0.002,
            "change_percent": 0.24,
            "timestamp": "2024-01-15T16:00:00Z"
        }
    """
    try:
        if source == "yahoo":
            data = await _fetch_yahoo_forex_data(from_currency, to_currency, period="1d")
            info = data["info"]
            hist = data["history"]
            
            if not hist:
                raise ForexDataError(f"No forex data available for {from_currency}/{to_currency}")
                
            latest = hist[-1] if isinstance(hist, list) else hist.iloc[-1]
            previous = hist[-2] if len(hist) > 1 else latest
            
            current_rate = float(latest.get("Close", 0))
            previous_rate = float(previous.get("Close", 0))
            
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": current_rate,
                "inverse_rate": 1 / current_rate if current_rate > 0 else 0,
                "change": current_rate - previous_rate,
                "change_percent": ((current_rate - previous_rate) / previous_rate * 100) if previous_rate > 0 else 0,
                "high": float(latest.get("High", 0)),
                "low": float(latest.get("Low", 0)),
                "volume": int(latest.get("Volume", 0)),
                "timestamp": datetime.now().isoformat() + "Z",
                "source": "yahoo"
            }
        elif source == "alpha_vantage":
            data = await _fetch_alpha_vantage_forex_data(from_currency, to_currency, "CURRENCY_EXCHANGE_RATE")
            rate_data = data["data"]
            
            if not rate_data:
                raise ForexDataError(f"No forex data available for {from_currency}/{to_currency}")
                
            current_rate = float(rate_data["5. Exchange Rate"])
            
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": current_rate,
                "inverse_rate": 1 / current_rate if current_rate > 0 else 0,
                "bid": float(rate_data.get("8. Bid Price", 0)),
                "ask": float(rate_data.get("9. Ask Price", 0)),
                "timestamp": rate_data.get("6. Last Refreshed", datetime.now().isoformat()),
                "source": "alpha_vantage"
            }
        else:
            raise ForexDataError(f"Unsupported source: {source}")
            
    except Exception as e:
        logger.error(f"Error in get_forex_rate for {from_currency}/{to_currency}: {e}")
        return {"error": str(e), "from_currency": from_currency, "to_currency": to_currency}


async def get_forex_history(
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
        
    Example:
        >>> await get_forex_history("USD", "EUR", period="1mo", interval="1d")
        {
            "from_currency": "USD",
            "to_currency": "EUR",
            "period": "1mo",
            "interval": "1d",
            "data": [
                {
                    "date": "2024-01-15",
                    "open": 0.845,
                    "high": 0.852,
                    "low": 0.843,
                    "close": 0.850,
                    "volume": 0
                },
                ...
            ]
        }
    """
    try:
        symbol = f"{from_currency}{to_currency}=X"
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise ForexDataError(f"No historical forex data available for {from_currency}/{to_currency}")
            
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
            "from_currency": from_currency,
            "to_currency": to_currency,
            "period": period,
            "interval": interval,
            "data": data,
            "count": len(data)
        }
        
    except Exception as e:
        logger.error(f"Error in get_forex_history for {from_currency}/{to_currency}: {e}")
        return {"error": str(e), "from_currency": from_currency, "to_currency": to_currency}


async def get_currency_list() -> Dict[str, Any]:
    """
    Get list of supported currencies with their information.
    
    Returns:
        Dictionary containing currency list and information
        
    Example:
        >>> await get_currency_list()
        {
            "currencies": [
                {
                    "code": "USD",
                    "name": "US Dollar",
                    "symbol": "$",
                    "type": "fiat"
                },
                {
                    "code": "EUR",
                    "name": "Euro",
                    "symbol": "€",
                    "type": "fiat"
                },
                ...
            ]
        }
    """
    try:
        # Major world currencies
        currencies = [
            {"code": "USD", "name": "US Dollar", "symbol": "$", "type": "fiat"},
            {"code": "EUR", "name": "Euro", "symbol": "€", "type": "fiat"},
            {"code": "GBP", "name": "British Pound", "symbol": "£", "type": "fiat"},
            {"code": "JPY", "name": "Japanese Yen", "symbol": "¥", "type": "fiat"},
            {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$", "type": "fiat"},
            {"code": "AUD", "name": "Australian Dollar", "symbol": "A$", "type": "fiat"},
            {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF", "type": "fiat"},
            {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥", "type": "fiat"},
            {"code": "INR", "name": "Indian Rupee", "symbol": "₹", "type": "fiat"},
            {"code": "BRL", "name": "Brazilian Real", "symbol": "R$", "type": "fiat"},
            {"code": "MXN", "name": "Mexican Peso", "symbol": "$", "type": "fiat"},
            {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$", "type": "fiat"},
            {"code": "HKD", "name": "Hong Kong Dollar", "symbol": "HK$", "type": "fiat"},
            {"code": "NOK", "name": "Norwegian Krone", "symbol": "kr", "type": "fiat"},
            {"code": "SEK", "name": "Swedish Krona", "symbol": "kr", "type": "fiat"},
            {"code": "KRW", "name": "South Korean Won", "symbol": "₩", "type": "fiat"},
            {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ$", "type": "fiat"},
            {"code": "RUB", "name": "Russian Ruble", "symbol": "₽", "type": "fiat"},
            {"code": "ZAR", "name": "South African Rand", "symbol": "R", "type": "fiat"},
            {"code": "TRY", "name": "Turkish Lira", "symbol": "₺", "type": "fiat"},
        ]
        
        return {
            "currencies": currencies,
            "count": len(currencies),
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_currency_list: {e}")
        return {"error": str(e)}


async def get_currency_converter(
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
        
    Example:
        >>> await get_currency_converter(100, "USD", "EUR")
        {
            "amount": 100.0,
            "from_currency": "USD",
            "to_currency": "EUR",
            "rate": 0.85,
            "converted_amount": 85.0,
            "timestamp": "2024-01-15T16:00:00Z"
        }
    """
    try:
        rate_data = await get_forex_rate(from_currency, to_currency, source)
        
        if "error" in rate_data:
            return rate_data
            
        rate = rate_data["rate"]
        converted_amount = amount * rate
        
        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "converted_amount": converted_amount,
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_currency_converter: {e}")
        return {"error": str(e), "amount": amount, "from_currency": from_currency, "to_currency": to_currency}
