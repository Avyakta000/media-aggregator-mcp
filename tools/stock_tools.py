"""Stock Market Tools for FinanceMCP

This module provides tools for fetching stock market data including prices,
quotes, historical data, and fundamental information.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import yfinance as yf
import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import settings
from .types import (
    StockPriceData, StockQuoteData, StockHistoryData, StockFundamentalsData,
    StockSearchResult, StockAnalysisData, StockPeriod, StockInterval, 
    DataSource, ApiResponse
)

logger = logging.getLogger(__name__)


class StockDataError(Exception):
    """Custom exception for stock data errors."""
    pass

async def _try_both_exchanges(symbol: str, func, *args, **kwargs) -> Dict[str, Any]:
    """
    Try to fetch data for a stock using both NSE and BSE exchanges.
    
    Args:
        symbol: Stock symbol without suffix
        func: Function to call (e.g., get_stock_price, get_stock_quote)
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Result from the first successful exchange, or error if both fail
    """
    # Try NSE first (more commonly used)
    try:
        nse_symbol = f"{symbol}.NS"
        result = await func(nse_symbol, *args, **kwargs)
        if "error" not in result:
            return result
    except Exception as e:
        logger.debug(f"NSE attempt failed for {symbol}: {e}")
    
    # Try BSE if NSE failed
    try:
        bse_symbol = f"{symbol}.BO"
        result = await func(bse_symbol, *args, **kwargs)
        if "error" not in result:
            return result
    except Exception as e:
        logger.debug(f"BSE attempt failed for {symbol}: {e}")
    
    # If both failed, return error
    return {
        "error": f"Could not find data for {symbol} on either NSE (.NS) or BSE (.BO)",
        "symbol": symbol,
        "tried_exchanges": [f"{symbol}.NS", f"{symbol}.BO"]
    }


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


def _calculate_technical_indicators(hist_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate technical indicators from historical data."""
    try:
        close_prices = hist_df['Close']
        
        # Moving averages
        ma20 = close_prices.rolling(window=20).mean().iloc[-1] if len(close_prices) >= 20 else None
        ma50 = close_prices.rolling(window=50).mean().iloc[-1] if len(close_prices) >= 50 else None
        ma200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else None
        
        # 52-week range
        high_52w = close_prices.max()
        low_52w = close_prices.min()
        
        # RSI calculation (14-period)
        if len(close_prices) >= 14:
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_14 = rsi.iloc[-1]
        else:
            rsi_14 = None
        
        # MACD calculation
        if len(close_prices) >= 26:
            ema12 = close_prices.ewm(span=12).mean()
            ema26 = close_prices.ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            macd_value = macd_line.iloc[-1]
            signal_value = signal_line.iloc[-1]
        else:
            macd_value = None
            signal_value = None
        
        # Trend signal
        trend_signal = "Neutral"
        if ma20 and ma50 and ma200:
            if close_prices.iloc[-1] > ma50 and ma50 > ma200:
                trend_signal = "Bullish (above 50d & 200d SMA)"
            elif close_prices.iloc[-1] < ma50 and ma50 < ma200:
                trend_signal = "Bearish (below 50d & 200d SMA)"
            elif close_prices.iloc[-1] > ma20 and ma20 > ma50:
                trend_signal = "Short-term Bullish"
            elif close_prices.iloc[-1] < ma20 and ma20 < ma50:
                trend_signal = "Short-term Bearish"
        
        return {
            "last_price": float(close_prices.iloc[-1]),
            "52w_range": [float(low_52w), float(high_52w)],
            "moving_averages": {
                "20d": float(ma20) if ma20 else None,
                "50d": float(ma50) if ma50 else None,
                "200d": float(ma200) if ma200 else None
            },
            "rsi_14": float(rsi_14) if rsi_14 else None,
            "macd": {
                "macd": float(macd_value) if macd_value else None,
                "signal": float(signal_value) if signal_value else None
            },
            "trend_signal": trend_signal
        }
    except Exception as e:
        logger.error(f"Error calculating technical indicators: {e}")
        return {}


def _generate_summary_analysis(fundamentals: Dict, technicals: Dict, info: Dict) -> Dict[str, Any]:
    """Generate summary analysis based on fundamentals and technicals."""
    strengths = []
    risks = []
    overall_view = "Neutral"
    
    try:
        # Valuation analysis
        pe_ratio = fundamentals.get("valuation", {}).get("PE")
        pb_ratio = fundamentals.get("valuation", {}).get("PB")
        debt_equity = fundamentals.get("financial_health", {}).get("DebtEquity")
        roe = fundamentals.get("profitability", {}).get("ROE")
        net_margin = fundamentals.get("profitability", {}).get("NetMargin")
        
        # Technical analysis
        last_price = technicals.get("last_price")
        ma50 = technicals.get("moving_averages", {}).get("50d")
        ma200 = technicals.get("moving_averages", {}).get("200d")
        rsi = technicals.get("rsi_14")
        
        # Strengths
        if pe_ratio and pe_ratio < 20:
            strengths.append("Reasonable valuation (low PE ratio)")
        if roe and roe > 15:
            strengths.append("Strong return on equity")
        if net_margin and net_margin > 10:
            strengths.append("Healthy profit margins")
        if last_price and ma50 and ma200 and last_price > ma50 and ma50 > ma200:
            strengths.append("Strong technical uptrend")
        
        # Risks
        if debt_equity and debt_equity > 1:
            risks.append("High debt levels")
        if pe_ratio and pe_ratio > 30:
            risks.append("High valuation (elevated PE ratio)")
        if rsi and rsi > 70:
            risks.append("Overbought conditions (high RSI)")
        if rsi and rsi < 30:
            risks.append("Oversold conditions (low RSI)")
        
        # Overall view
        if len(strengths) > len(risks) and last_price and ma50 and last_price > ma50:
            overall_view = "Moderately bullish in near term; attractive long-term fundamentals"
        elif len(risks) > len(strengths) and last_price and ma50 and last_price < ma50:
            overall_view = "Moderately bearish; consider waiting for better entry point"
        elif len(strengths) > len(risks):
            overall_view = "Fundamentally sound; monitor technical levels"
        else:
            overall_view = "Mixed signals; requires careful analysis"
            
    except Exception as e:
        logger.error(f"Error generating summary analysis: {e}")
        strengths = ["Analysis incomplete"]
        risks = ["Data limitations"]
        overall_view = "Analysis unavailable"
    
    return {
        "strengths": strengths,
        "risks": risks,
        "overall_view": overall_view
    }


async def analyze_stock(
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
        Dictionary containing comprehensive stock analysis
        
    Example:
        >>> await analyze_stock("RELIANCE")
        {
            "symbol": "RELIANCE.NS",
            "company_profile": {
                "name": "Reliance Industries Limited",
                "sector": "Energy",
                "industry": "Oil & Gas Refining & Marketing",
                "market_cap": "19.2T INR",
                "description": "Reliance Industries Limited engages in ...",
                "exchange": "NSE"
            },
            "fundamentals": {
                "valuation": {"PE": 22.1, "PB": 3.4, "PEG": 1.2},
                "profitability": {"ROE": 15.6, "ROA": 7.3, "NetMargin": 10.2},
                "growth": {"RevenueYoY": 12.4, "EPSYoY": 8.9},
                "financial_health": {"DebtEquity": 0.45, "CurrentRatio": 1.3}
            },
            "technicals": {
                "last_price": 2365.2,
                "52w_range": [2100, 2450],
                "moving_averages": {"20d": 2330, "50d": 2310, "200d": 2250},
                "rsi_14": 62.3,
                "macd": {"macd": 4.2, "signal": 2.1},
                "trend_signal": "Bullish (above 50d & 200d SMA)"
            },
            "summary": {
                "strengths": ["Strong revenue growth", "Leadership in energy sector"],
                "risks": ["Oil price dependency", "High debt levels"],
                "overall_view": "Moderately bullish in near term; attractive long-term fundamentals"
            },
            "as_of": "2025-08-29"
        }
    """
    # If no exchange suffix is provided, try both NSE and BSE
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        return await _try_both_exchanges(symbol, analyze_stock, period, interval)
    
    try:
        # Fetch comprehensive data
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise StockDataError(f"No data found for symbol: {symbol}")
        
        # Company Profile
        company_profile = {
            "name": info.get("longName", info.get("shortName", symbol)),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
            "description": info.get("longBusinessSummary", ""),
            "exchange": info.get("exchange", ""),
            "website": info.get("website", ""),
            "employees": info.get("fullTimeEmployees", 0)
        }
        
        # Fundamentals
        fundamentals = {
            "valuation": {
                "PE": info.get("trailingPE"),
                "PB": info.get("priceToBook"),
                "PEG": info.get("pegRatio"),
                "PS": info.get("priceToSalesTrailing12Months"),
                "EV_EBITDA": info.get("enterpriseToEbitda")
            },
            "profitability": {
                "ROE": info.get("returnOnEquity"),
                "ROA": info.get("returnOnAssets"),
                "NetMargin": info.get("profitMargins"),
                "OperatingMargin": info.get("operatingMargins"),
                "GrossMargin": info.get("grossMargins")
            },
            "growth": {
                "RevenueYoY": info.get("revenueGrowth"),
                "EPSYoY": info.get("earningsGrowth"),
                "RevenuePerShare": info.get("revenuePerShare"),
                "BookValue": info.get("bookValue")
            },
            "financial_health": {
                "DebtEquity": info.get("debtToEquity"),
                "CurrentRatio": info.get("currentRatio"),
                "QuickRatio": info.get("quickRatio"),
                "InterestCoverage": info.get("interestCoverage")
            }
        }
        
        # Technical Analysis
        technicals = _calculate_technical_indicators(hist)
        
        # Generate Summary
        summary = _generate_summary_analysis(fundamentals, technicals, info)
        
        return {
            "symbol": symbol,
            "company_profile": company_profile,
            "fundamentals": fundamentals,
            "technicals": technicals,
            "summary": summary,
            "as_of": datetime.now().strftime("%Y-%m-%d")
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_stock for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}


async def get_stock_price(
    symbol: str,
    source: DataSource = "yahoo"
) -> ApiResponse:
    """
    Get current stock price for Indian stocks.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "PNB.BO")
               If no exchange suffix is provided, will automatically try NSE (.NS) first, then BSE (.BO)
        source: Data source ("yahoo" or "alpha_vantage")
    
    Returns:
        Dictionary containing current price and basic information
        
    Example:
        >>> await get_stock_price("RELIANCE")      # Will try RELIANCE.NS first
        >>> await get_stock_price("RELIANCE.NS")   # Uses NSE explicitly
        >>> await get_stock_price("PNB.BO")        # Uses BSE explicitly
        {
            "symbol": "RELIANCE.NS",
            "price": 2450.75,
            "change": 30.65,
            "change_percent": 1.27,
            "volume": 2345678,
            "market_cap": 16500000000000,
            "timestamp": "2024-01-15T16:00:00Z"
        }
    """
    # If no exchange suffix is provided, try both NSE and BSE
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        return await _try_both_exchanges(symbol, get_stock_price, source)
    
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


async def get_stock_quote(symbol: str) -> ApiResponse:
    """
    Get comprehensive stock quote information for Indian stocks.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "PNB.BO")
               If no exchange suffix is provided, will automatically try NSE (.NS) first, then BSE (.BO)
    
    Returns:
        Dictionary containing detailed quote information
        
    Example:
        >>> await get_stock_quote("RELIANCE")      # Will try RELIANCE.NS first
        >>> await get_stock_quote("RELIANCE.NS")   # Uses NSE explicitly
        >>> await get_stock_quote("PNB.BO")        # Uses BSE explicitly
        {
            "symbol": "RELIANCE.NS",
            "company_name": "Reliance Industries Limited",
            "current_price": 2450.75,
            "previous_close": 2420.10,
            "open": 2430.50,
            "day_high": 2460.00,
            "day_low": 2410.75,
            "volume": 2345678,
            "market_cap": 16500000000000,
            "pe_ratio": 18.5,
            "dividend_yield": 0.45,
            "sector": "Oil & Gas",
            "industry": "Refineries"
        }
    """
    # If no exchange suffix is provided, try both NSE and BSE
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        return await _try_both_exchanges(symbol, get_stock_quote)
    
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
    period: StockPeriod = "1mo",
    interval: StockInterval = "1d"
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
        
    Example:
        >>> await get_stock_history("RELIANCE", period="1mo", interval="1d")
        >>> await get_stock_history("RELIANCE.NS", period="1mo", interval="1d")
        >>> await get_stock_history("PNB.BO", period="1mo", interval="1d")
        {
            "symbol": "RELIANCE.NS",
            "period": "1mo",
            "interval": "1d",
            "data": [
                {
                    "date": "2024-01-15",
                    "open": 2430.50,
                    "high": 2460.00,
                    "low": 2410.75,
                    "close": 2450.75,
                    "volume": 2345678
                },
                ...
            ]
        }
    """
    # If no exchange suffix is provided, try both NSE and BSE
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        return await _try_both_exchanges(symbol, get_stock_history, period, interval)
    
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


async def get_stock_fundamentals(symbol: str) -> ApiResponse:
    """
    Get fundamental financial data for Indian stocks.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "PNB.BO")
               If no exchange suffix is provided, will automatically try NSE (.NS) first, then BSE (.BO)
    
    Returns:
        Dictionary containing fundamental data
        
    Example:
        >>> await get_stock_fundamentals("RELIANCE")      # Will try RELIANCE.NS first
        >>> await get_stock_fundamentals("RELIANCE.NS")   # Uses NSE explicitly
        >>> await get_stock_fundamentals("PNB.BO")        # Uses BSE explicitly
        {
            "symbol": "RELIANCE.NS",
            "financial_metrics": {
                "market_cap": 16500000000000,
                "enterprise_value": 17000000000000,
                "pe_ratio": 18.5,
                "forward_pe": 17.2,
                "price_to_book": 2.2,
                "debt_to_equity": 0.25,
                "current_ratio": 1.2,
                "return_on_equity": 0.15
            },
            "dividend_info": {
                "dividend_yield": 0.45,
                "dividend_rate": 11.0,
                "payout_ratio": 0.08
            }
        }
    """
    # If no exchange suffix is provided, try both NSE and BSE
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        return await _try_both_exchanges(symbol, get_stock_fundamentals)
    
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


async def search_stocks(query: str, limit: int = 10) -> ApiResponse:
    """
    Search for Indian stocks by company name or symbol.
    
    Args:
        query: Search query (company name or symbol)
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results (prioritizes Indian stocks)
        
    Example:
        >>> await search_stocks("Reliance", limit=5)
        >>> await search_stocks("TCS", limit=5)
        >>> await search_stocks("HDFC", limit=5)
        {
            "query": "Reliance",
            "results": [
                {
                    "symbol": "RELIANCE.NS",
                    "name": "Reliance Industries Limited",
                    "exchange": "NSE",
                    "type": "Common Stock",
                    "market_cap": 16500000000000,
                    "current_price": 2450.75
                },
                ...
            ]
        }
    """
    try:
        # Use Yahoo Finance search
        search_results = yf.Tickers(query)
        
        results = []
        indian_results = []
        other_results = []
        count = 0
        
        for ticker in search_results.tickers:
            if count >= limit:
                break
                
            try:
                info = ticker.info
                if info.get("regularMarketPrice"):
                    result = {
                        "symbol": info.get("symbol", ""),
                        "name": info.get("longName", info.get("shortName", "")),
                        "exchange": info.get("exchange", ""),
                        "type": info.get("quoteType", ""),
                        "market_cap": info.get("marketCap", 0),
                        "current_price": info.get("regularMarketPrice", 0)
                    }
                    
                    # Prioritize Indian stocks (NSE and BSE)
                    symbol = info.get("symbol", "")
                    if symbol.endswith('.NS') or symbol.endswith('.BO'):
                        indian_results.append(result)
                    else:
                        other_results.append(result)
                        
                    count += 1
            except Exception as e:
                logger.warning(f"Error processing ticker {ticker}: {e}")
                continue
        
        # Combine results with Indian stocks first
        results = indian_results + other_results
        results = results[:limit]  # Ensure we don't exceed the limit
                
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in search_stocks for query '{query}': {e}")
        return {"error": str(e), "query": query}
