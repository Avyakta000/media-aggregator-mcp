"""Macroeconomic Tools for FinanceMCP

This module provides tools for fetching macroeconomic data including
economic indicators, Federal Reserve rates, inflation data, and GDP data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pandas as pd
from fredapi import Fred
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import settings
from .types import (
    EconomicIndicatorData, FedRatesData, InflationData, GDPData,
    UnemploymentData, PopularIndicatorsData, ApiResponse
)

logger = logging.getLogger(__name__)


class MacroDataError(Exception):
    """Custom exception for macroeconomic data errors."""
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _fetch_fred_data(series_id: str, observation_start: Optional[str] = None, observation_end: Optional[str] = None) -> Dict[str, Any]:
    """Fetch data from FRED API with retry logic."""
    if not settings.fred_api_key:
        raise MacroDataError("FRED API key not configured")
    
    try:
        fred = Fred(api_key=settings.fred_api_key)
        
        # Get series info
        series_info = fred.get_series_info(series_id)
        
        # Get observations
        observations = fred.get_series(
            series_id,
            observation_start=observation_start,
            observation_end=observation_end
        )
        
        return {
            "series_info": series_info,
            "observations": observations.to_dict() if not observations.empty else {}
        }
    except Exception as e:
        logger.error(f"Error fetching FRED data for {series_id}: {e}")
        raise MacroDataError(f"Failed to fetch FRED data for {series_id}: {str(e)}")


async def get_economic_indicator(
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
        
    Example:
        >>> await get_economic_indicator("GDP", observation_start="2020-01-01")
        {
            "series_id": "GDP",
            "title": "Gross Domestic Product",
            "units": "Billions of Dollars",
            "frequency": "Quarterly",
            "data": [
                {
                    "date": "2023-10-01",
                    "value": 25000.0,
                    "realtime_start": "2024-01-15",
                    "realtime_end": "2024-01-15"
                },
                ...
            ]
        }
    """
    try:
        data = await _fetch_fred_data(series_id, observation_start, observation_end)
        series_info = data["series_info"]
        observations = data["observations"]
        
        # Convert observations to list format
        data_points = []
        for date, value in observations.items():
            data_points.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": float(value) if pd.notna(value) else None,
                "realtime_start": datetime.now().strftime("%Y-%m-%d"),
                "realtime_end": datetime.now().strftime("%Y-%m-%d")
            })
        
        return {
            "series_id": series_id,
            "title": series_info.get("title", ""),
            "units": series_info.get("units", ""),
            "frequency": series_info.get("frequency", ""),
            "seasonal_adjustment": series_info.get("seasonal_adjustment", ""),
            "last_updated": series_info.get("last_updated", ""),
            "notes": series_info.get("notes", ""),
            "data": data_points,
            "count": len(data_points)
        }
        
    except Exception as e:
        logger.error(f"Error in get_economic_indicator for {series_id}: {e}")
        return {"error": str(e), "series_id": series_id}


async def get_fed_rates() -> ApiResponse:
    """
    Get Federal Reserve interest rates.
    
    Returns:
        Dictionary containing Federal Reserve rates data
        
    Example:
        >>> await get_fed_rates()
        {
            "rates": {
                "federal_funds_rate": {
                    "current": 5.25,
                    "previous": 5.00,
                    "change": 0.25,
                    "last_updated": "2024-01-15"
                },
                "discount_rate": {
                    "current": 5.50,
                    "previous": 5.25,
                    "change": 0.25,
                    "last_updated": "2024-01-15"
                }
            }
        }
    """
    try:
        # Federal Funds Rate (FEDFUNDS)
        fed_funds_data = await _fetch_fred_data("FEDFUNDS", observation_start=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        fed_funds_obs = fed_funds_data["observations"]
        
        # Discount Rate (DPRIME)
        discount_data = await _fetch_fred_data("DPRIME", observation_start=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        discount_obs = discount_data["observations"]
        
        # Get latest and previous values
        fed_funds_values = list(fed_funds_obs.values())
        discount_values = list(discount_obs.values())
        
        current_fed_funds = float(fed_funds_values[-1]) if fed_funds_values and pd.notna(fed_funds_values[-1]) else None
        previous_fed_funds = float(fed_funds_values[-2]) if len(fed_funds_values) > 1 and pd.notna(fed_funds_values[-2]) else None
        
        current_discount = float(discount_values[-1]) if discount_values and pd.notna(discount_values[-1]) else None
        previous_discount = float(discount_values[-2]) if len(discount_values) > 1 and pd.notna(discount_values[-2]) else None
        
        return {
            "rates": {
                "federal_funds_rate": {
                    "current": current_fed_funds,
                    "previous": previous_fed_funds,
                    "change": current_fed_funds - previous_fed_funds if current_fed_funds and previous_fed_funds else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                },
                "discount_rate": {
                    "current": current_discount,
                    "previous": previous_discount,
                    "change": current_discount - previous_discount if current_discount and previous_discount else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                }
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_fed_rates: {e}")
        return {"error": str(e)}


async def get_inflation_data() -> ApiResponse:
    """
    Get inflation data including CPI and PCE.
    
    Returns:
        Dictionary containing inflation data
        
    Example:
        >>> await get_inflation_data()
        {
            "inflation_indicators": {
                "cpi_all_urban": {
                    "current": 307.051,
                    "year_over_year_change": 3.1,
                    "month_over_month_change": 0.3,
                    "last_updated": "2023-12-01"
                },
                "core_cpi": {
                    "current": 310.196,
                    "year_over_year_change": 3.9,
                    "month_over_month_change": 0.3,
                    "last_updated": "2023-12-01"
                }
            }
        }
    """
    try:
        # Consumer Price Index for All Urban Consumers (CPIAUCSL)
        cpi_data = await _fetch_fred_data("CPIAUCSL", observation_start=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        cpi_obs = cpi_data["observations"]
        
        # Core CPI (CPILFESL)
        core_cpi_data = await _fetch_fred_data("CPILFESL", observation_start=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        core_cpi_obs = core_cpi_data["observations"]
        
        # Personal Consumption Expenditures (PCEPI)
        pce_data = await _fetch_fred_data("PCEPI", observation_start=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        pce_obs = pce_data["observations"]
        
        # Calculate year-over-year and month-over-month changes
        cpi_values = list(cpi_obs.values())
        core_cpi_values = list(core_cpi_obs.values())
        pce_values = list(pce_obs.values())
        
        current_cpi = float(cpi_values[-1]) if cpi_values and pd.notna(cpi_values[-1]) else None
        year_ago_cpi = float(cpi_values[-13]) if len(cpi_values) > 12 and pd.notna(cpi_values[-13]) else None
        month_ago_cpi = float(cpi_values[-2]) if len(cpi_values) > 1 and pd.notna(cpi_values[-2]) else None
        
        current_core_cpi = float(core_cpi_values[-1]) if core_cpi_values and pd.notna(core_cpi_values[-1]) else None
        year_ago_core_cpi = float(core_cpi_values[-13]) if len(core_cpi_values) > 12 and pd.notna(core_cpi_values[-13]) else None
        month_ago_core_cpi = float(core_cpi_values[-2]) if len(core_cpi_values) > 1 and pd.notna(core_cpi_values[-2]) else None
        
        current_pce = float(pce_values[-1]) if pce_values and pd.notna(pce_values[-1]) else None
        year_ago_pce = float(pce_values[-13]) if len(pce_values) > 12 and pd.notna(pce_values[-13]) else None
        month_ago_pce = float(pce_values[-2]) if len(pce_values) > 1 and pd.notna(pce_values[-2]) else None
        
        return {
            "inflation_indicators": {
                "cpi_all_urban": {
                    "current": current_cpi,
                    "year_over_year_change": ((current_cpi - year_ago_cpi) / year_ago_cpi * 100) if current_cpi and year_ago_cpi else None,
                    "month_over_month_change": ((current_cpi - month_ago_cpi) / month_ago_cpi * 100) if current_cpi and month_ago_cpi else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                },
                "core_cpi": {
                    "current": current_core_cpi,
                    "year_over_year_change": ((current_core_cpi - year_ago_core_cpi) / year_ago_core_cpi * 100) if current_core_cpi and year_ago_core_cpi else None,
                    "month_over_month_change": ((current_core_cpi - month_ago_core_cpi) / month_ago_core_cpi * 100) if current_core_cpi and month_ago_core_cpi else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                },
                "pce_price_index": {
                    "current": current_pce,
                    "year_over_year_change": ((current_pce - year_ago_pce) / year_ago_pce * 100) if current_pce and year_ago_pce else None,
                    "month_over_month_change": ((current_pce - month_ago_pce) / month_ago_pce * 100) if current_pce and month_ago_pce else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                }
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_inflation_data: {e}")
        return {"error": str(e)}


async def get_gdp_data() -> ApiResponse:
    """
    Get GDP data including real and nominal GDP.
    
    Returns:
        Dictionary containing GDP data
        
    Example:
        >>> await get_gdp_data()
        {
            "gdp_indicators": {
                "real_gdp": {
                    "current": 25000.0,
                    "previous": 24800.0,
                    "quarter_over_quarter_change": 0.8,
                    "year_over_year_change": 2.1,
                    "last_updated": "2023-10-01"
                },
                "nominal_gdp": {
                    "current": 27000.0,
                    "previous": 26800.0,
                    "quarter_over_quarter_change": 0.7,
                    "year_over_year_change": 3.2,
                    "last_updated": "2023-10-01"
                }
            }
        }
    """
    try:
        # Real GDP (GDPC1)
        real_gdp_data = await _fetch_fred_data("GDPC1", observation_start=(datetime.now() - timedelta(days=365*2)).strftime("%Y-%m-%d"))
        real_gdp_obs = real_gdp_data["observations"]
        
        # Nominal GDP (GDP)
        nominal_gdp_data = await _fetch_fred_data("GDP", observation_start=(datetime.now() - timedelta(days=365*2)).strftime("%Y-%m-%d"))
        nominal_gdp_obs = nominal_gdp_data["observations"]
        
        # Calculate quarter-over-quarter and year-over-year changes
        real_gdp_values = list(real_gdp_obs.values())
        nominal_gdp_values = list(nominal_gdp_obs.values())
        
        current_real_gdp = float(real_gdp_values[-1]) if real_gdp_values and pd.notna(real_gdp_values[-1]) else None
        previous_real_gdp = float(real_gdp_values[-2]) if len(real_gdp_values) > 1 and pd.notna(real_gdp_values[-2]) else None
        year_ago_real_gdp = float(real_gdp_values[-5]) if len(real_gdp_values) > 4 and pd.notna(real_gdp_values[-5]) else None
        
        current_nominal_gdp = float(nominal_gdp_values[-1]) if nominal_gdp_values and pd.notna(nominal_gdp_values[-1]) else None
        previous_nominal_gdp = float(nominal_gdp_values[-2]) if len(nominal_gdp_values) > 1 and pd.notna(nominal_gdp_values[-2]) else None
        year_ago_nominal_gdp = float(nominal_gdp_values[-5]) if len(nominal_gdp_values) > 4 and pd.notna(nominal_gdp_values[-5]) else None
        
        return {
            "gdp_indicators": {
                "real_gdp": {
                    "current": current_real_gdp,
                    "previous": previous_real_gdp,
                    "quarter_over_quarter_change": ((current_real_gdp - previous_real_gdp) / previous_real_gdp * 100) if current_real_gdp and previous_real_gdp else None,
                    "year_over_year_change": ((current_real_gdp - year_ago_real_gdp) / year_ago_real_gdp * 100) if current_real_gdp and year_ago_real_gdp else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                },
                "nominal_gdp": {
                    "current": current_nominal_gdp,
                    "previous": previous_nominal_gdp,
                    "quarter_over_quarter_change": ((current_nominal_gdp - previous_nominal_gdp) / previous_nominal_gdp * 100) if current_nominal_gdp and previous_nominal_gdp else None,
                    "year_over_year_change": ((current_nominal_gdp - year_ago_nominal_gdp) / year_ago_nominal_gdp * 100) if current_nominal_gdp and year_ago_nominal_gdp else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                }
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_gdp_data: {e}")
        return {"error": str(e)}


async def get_unemployment_data() -> ApiResponse:
    """
    Get unemployment data including unemployment rate and labor force participation.
    
    Returns:
        Dictionary containing unemployment data
        
    Example:
        >>> await get_unemployment_data()
        {
            "unemployment_indicators": {
                "unemployment_rate": {
                    "current": 3.7,
                    "previous": 3.8,
                    "change": -0.1,
                    "last_updated": "2023-12-01"
                },
                "labor_force_participation": {
                    "current": 62.5,
                    "previous": 62.4,
                    "change": 0.1,
                    "last_updated": "2023-12-01"
                }
            }
        }
    """
    try:
        # Unemployment Rate (UNRATE)
        unemployment_data = await _fetch_fred_data("UNRATE", observation_start=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        unemployment_obs = unemployment_data["observations"]
        
        # Labor Force Participation Rate (CIVPART)
        participation_data = await _fetch_fred_data("CIVPART", observation_start=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
        participation_obs = participation_data["observations"]
        
        # Get latest and previous values
        unemployment_values = list(unemployment_obs.values())
        participation_values = list(participation_obs.values())
        
        current_unemployment = float(unemployment_values[-1]) if unemployment_values and pd.notna(unemployment_values[-1]) else None
        previous_unemployment = float(unemployment_values[-2]) if len(unemployment_values) > 1 and pd.notna(unemployment_values[-2]) else None
        
        current_participation = float(participation_values[-1]) if participation_values and pd.notna(participation_values[-1]) else None
        previous_participation = float(participation_values[-2]) if len(participation_values) > 1 and pd.notna(participation_values[-2]) else None
        
        return {
            "unemployment_indicators": {
                "unemployment_rate": {
                    "current": current_unemployment,
                    "previous": previous_unemployment,
                    "change": current_unemployment - previous_unemployment if current_unemployment and previous_unemployment else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                },
                "labor_force_participation": {
                    "current": current_participation,
                    "previous": previous_participation,
                    "change": current_participation - previous_participation if current_participation and previous_participation else None,
                    "last_updated": datetime.now().strftime("%Y-%m-%d")
                }
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_unemployment_data: {e}")
        return {"error": str(e)}


async def get_popular_indicators() -> ApiResponse:
    """
    Get list of popular economic indicators with their FRED series IDs.
    
    Returns:
        Dictionary containing popular indicators list
        
    Example:
        >>> await get_popular_indicators()
        {
            "indicators": [
                {
                    "series_id": "GDP",
                    "title": "Gross Domestic Product",
                    "category": "National Accounts",
                    "frequency": "Quarterly"
                },
                {
                    "series_id": "UNRATE",
                    "title": "Unemployment Rate",
                    "category": "Labor Market",
                    "frequency": "Monthly"
                },
                ...
            ]
        }
    """
    try:
        popular_indicators = [
            {"series_id": "GDP", "title": "Gross Domestic Product", "category": "National Accounts", "frequency": "Quarterly"},
            {"series_id": "GDPC1", "title": "Real Gross Domestic Product", "category": "National Accounts", "frequency": "Quarterly"},
            {"series_id": "UNRATE", "title": "Unemployment Rate", "category": "Labor Market", "frequency": "Monthly"},
            {"series_id": "CPIAUCSL", "title": "Consumer Price Index for All Urban Consumers", "category": "Prices", "frequency": "Monthly"},
            {"series_id": "CPILFESL", "title": "Consumer Price Index for All Urban Consumers: All Items Less Food and Energy", "category": "Prices", "frequency": "Monthly"},
            {"series_id": "PCEPI", "title": "Personal Consumption Expenditures: Chain-type Price Index", "category": "Prices", "frequency": "Monthly"},
            {"series_id": "FEDFUNDS", "title": "Federal Funds Effective Rate", "category": "Interest Rates", "frequency": "Monthly"},
            {"series_id": "DGS10", "title": "10-Year Treasury Constant Maturity Rate", "category": "Interest Rates", "frequency": "Daily"},
            {"series_id": "DGS2", "title": "2-Year Treasury Constant Maturity Rate", "category": "Interest Rates", "frequency": "Daily"},
            {"series_id": "CIVPART", "title": "Labor Force Participation Rate", "category": "Labor Market", "frequency": "Monthly"},
            {"series_id": "PAYEMS", "title": "Total Nonfarm Payrolls", "category": "Labor Market", "frequency": "Monthly"},
            {"series_id": "INDPRO", "title": "Industrial Production: Total Index", "category": "Production", "frequency": "Monthly"},
            {"series_id": "RSXFS", "title": "Advance Retail Sales: Retail and Food Services", "category": "Consumption", "frequency": "Monthly"},
            {"series_id": "HOUST", "title": "Housing Starts: Total: New Privately Owned Housing Units Started", "category": "Housing", "frequency": "Monthly"},
            {"series_id": "M2SL", "title": "M2 Money Stock", "category": "Money Supply", "frequency": "Monthly"},
        ]
        
        return {
            "indicators": popular_indicators,
            "count": len(popular_indicators),
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error in get_popular_indicators: {e}")
        return {"error": str(e)}
