"""Type Definitions for FinanceMCP

This module contains type definitions and data structures used across
the FinanceMCP server modules.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime


# ==================== STOCK MARKET TYPES ====================

class StockPriceData:
    """Type definition for stock price data"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[int]
    timestamp: str
    source: str


class StockQuoteData:
    """Type definition for comprehensive stock quote data"""
    symbol: str
    company_name: str
    current_price: float
    previous_close: float
    open: float
    day_high: float
    day_low: float
    volume: int
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    sector: Optional[str]
    industry: Optional[str]
    timestamp: str


class StockHistoryData:
    """Type definition for historical stock data"""
    symbol: str
    period: str
    interval: str
    data: List[Dict[str, Any]]
    count: int


class StockFundamentalsData:
    """Type definition for stock fundamental data"""
    symbol: str
    financial_metrics: Dict[str, Any]
    dividend_info: Dict[str, Any]
    growth_metrics: Dict[str, Any]
    timestamp: str


class StockSearchResult:
    """Type definition for stock search result"""
    symbol: str
    name: str
    exchange: str
    type: str
    market_cap: Optional[int]
    current_price: Optional[float]


class StockAnalysisData:
    """Type definition for comprehensive stock analysis"""
    symbol: str
    company_profile: Dict[str, Any]
    fundamentals: Dict[str, Any]
    technicals: Dict[str, Any]
    summary: Dict[str, Any]
    as_of: str


# ==================== MACROECONOMIC TYPES ====================

class EconomicIndicatorData:
    """Type definition for economic indicator data"""
    series_id: str
    title: str
    units: str
    frequency: str
    seasonal_adjustment: Optional[str]
    last_updated: str
    notes: Optional[str]
    data: List[Dict[str, Any]]
    count: int


class FedRatesData:
    """Type definition for Federal Reserve rates data"""
    rates: Dict[str, Dict[str, Any]]
    timestamp: str


class InflationData:
    """Type definition for inflation data"""
    inflation_indicators: Dict[str, Dict[str, Any]]
    timestamp: str


class GDPData:
    """Type definition for GDP data"""
    gdp_indicators: Dict[str, Dict[str, Any]]
    timestamp: str


class UnemploymentData:
    """Type definition for unemployment data"""
    unemployment_indicators: Dict[str, Dict[str, Any]]
    timestamp: str


class PopularIndicatorsData:
    """Type definition for popular indicators data"""
    indicators: List[Dict[str, str]]
    count: int
    timestamp: str


# ==================== COMMON TYPES ====================

class ErrorResponse:
    """Type definition for error responses"""
    error: str
    timestamp: str
    context: Dict[str, Any]


# ==================== TYPE ALIASES ====================

# Stock market period types
StockPeriod = Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

# Stock market interval types
StockInterval = Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]

# Data source types
DataSource = Literal["yahoo", "alpha_vantage"]

# Exchange types
Exchange = Literal["NSE", "BSE"]

# Currency types
Currency = Literal["INR", "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "BRL", "MXN", "SGD", "HKD", "NOK", "SEK", "KRW", "NZD", "RUB", "ZAR", "TRY"]

# Response types
ApiResponse = Union[Dict[str, Any], ErrorResponse]
