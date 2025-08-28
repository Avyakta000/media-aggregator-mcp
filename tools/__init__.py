"""FinanceMCP Tools Package

This package contains all financial data tools for the FinanceMCP server.
"""

from .stock_tools import *
from .forex_tools import *
from .crypto_tools import *
from .macro_tools import *

__all__ = [
    # Stock tools
    "get_stock_price",
    "get_stock_quote",
    "get_stock_history",
    "get_stock_fundamentals",
    "search_stocks",
    
    # Forex tools
    "get_forex_rate",
    "get_forex_history",
    "get_currency_list",
    
    # Crypto tools
    "get_crypto_price",
    "get_crypto_history",
    "get_crypto_list",
    
    # Macro tools
    "get_economic_indicator",
    "get_fed_rates",
    "get_inflation_data",
    "get_gdp_data",
]
