"""
FinanceMCP Usage Examples

This file demonstrates how AI agents can use the FinanceMCP server
to access financial data and perform market analysis.
"""

import asyncio
import json
from typing import Dict, Any

# Example functions that AI agents would call through the MCP server
# These simulate the actual tool calls that would be made

async def example_stock_analysis():
    """Example: Comprehensive stock market analysis"""
    print("=== STOCK MARKET ANALYSIS EXAMPLE ===")
    
    # Get Reliance stock quote (demonstrating automatic suffix handling)
    reliance_quote = {
        "symbol": "RELIANCE.NS",  # Could also pass "RELIANCE" and it would auto-add .NS
        "company_name": "Reliance Industries Limited",
        "current_price": 2450.75,
        "previous_close": 2420.10,
        "change": 30.65,
        "change_percent": 1.27,
        "volume": 2345678,
        "market_cap": 16500000000000,
        "pe_ratio": 18.5,
        "dividend_yield": 0.45,
        "sector": "Oil & Gas",
        "industry": "Refineries"
    }
    
    print(f"📈 {reliance_quote['company_name']} ({reliance_quote['symbol']})")
    print(f"   Current Price: ₹{reliance_quote['current_price']}")
    print(f"   Change: ₹{reliance_quote['change']} ({reliance_quote['change_percent']}%)")
    print(f"   Market Cap: ₹{reliance_quote['market_cap']:,}")
    print(f"   P/E Ratio: {reliance_quote['pe_ratio']}")
    print(f"   Dividend Yield: {reliance_quote['dividend_yield']}%")
    
    # Get historical data
    historical_data = {
        "symbol": "RELIANCE.NS",
        "period": "1mo",
        "interval": "1d",
        "data": [
            {"date": "2024-01-15", "close": 2450.75, "volume": 2345678},
            {"date": "2024-01-14", "close": 2420.10, "volume": 2154321},
            {"date": "2024-01-13", "close": 2415.85, "volume": 2123456}
        ]
    }
    
    print(f"\n📊 Historical Data (1 month):")
    for point in historical_data['data'][:3]:
        print(f"   {point['date']}: ₹{point['close']} (Volume: {point['volume']:,})")


async def example_macroeconomic_analysis():
    """Example: Macroeconomic indicators analysis"""
    print("\n=== MACROECONOMIC ANALYSIS EXAMPLE ===")
    
    # Get Federal Reserve rates
    fed_rates = {
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
    
    print(f"🏦 Federal Reserve Rates")
    print(f"   Federal Funds Rate: {fed_rates['rates']['federal_funds_rate']['current']}%")
    print(f"   Discount Rate: {fed_rates['rates']['discount_rate']['current']}%")
    
    # Get inflation data
    inflation_data = {
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
    
    print(f"\n📊 Inflation Indicators")
    print(f"   CPI (All Urban): {inflation_data['inflation_indicators']['cpi_all_urban']['year_over_year_change']}% YoY")
    print(f"   Core CPI: {inflation_data['inflation_indicators']['core_cpi']['year_over_year_change']}% YoY")
    
    # Get GDP data
    gdp_data = {
        "gdp_indicators": {
            "real_gdp": {
                "current": 25000.0,
                "previous": 24800.0,
                "quarter_over_quarter_change": 0.8,
                "year_over_year_change": 2.1,
                "last_updated": "2023-10-01"
            }
        }
    }
    
    print(f"\n📈 GDP Data")
    print(f"   Real GDP: ${gdp_data['gdp_indicators']['real_gdp']['current']:,}B")
    print(f"   QoQ Change: {gdp_data['gdp_indicators']['real_gdp']['quarter_over_quarter_change']}%")
    print(f"   YoY Change: {gdp_data['gdp_indicators']['real_gdp']['year_over_year_change']}%")


async def example_comprehensive_market_analysis():
    """Example: Comprehensive market analysis combining multiple data sources"""
    print("\n=== COMPREHENSIVE MARKET ANALYSIS EXAMPLE ===")
    
    # Simulate getting data from multiple sources
    market_summary = {
        "timestamp": "2024-01-15T16:00:00Z",
        "equity_markets": {
            "nifty50": {"symbol": "^NSEI", "price": 22500.50, "change": 125.30, "change_percent": 0.56},
            "sensex": {"symbol": "^BSESN", "price": 74200.75, "change": 245.20, "change_percent": 0.33},
            "banknifty": {"symbol": "^NSEBANK", "price": 48500.25, "change": 150.75, "change_percent": 0.31}
        },
        "macro_indicators": {
            "fed_funds_rate": 5.25,
            "inflation_cpi": 3.1,
            "unemployment_rate": 3.7,
            "gdp_growth": 2.1
        }
    }
    
    print(f"🌍 Indian Market Summary - {market_summary['timestamp']}")
    
    print(f"\n📈 Equity Markets:")
    for index, data in market_summary['equity_markets'].items():
        print(f"   {index.upper()}: ₹{data['price']:,} ({data['change']:+} / {data['change_percent']:+.2f}%)")
    
    print(f"\n🏦 Macroeconomic Indicators:")
    print(f"   Federal Funds Rate: {market_summary['macro_indicators']['fed_funds_rate']}%")
    print(f"   Inflation (CPI): {market_summary['macro_indicators']['inflation_cpi']}%")
    print(f"   Unemployment Rate: {market_summary['macro_indicators']['unemployment_rate']}%")
    print(f"   GDP Growth: {market_summary['macro_indicators']['gdp_growth']}%")


async def example_ai_agent_workflow():
    """Example: How an AI agent would use the FinanceMCP server"""
    print("\n=== AI AGENT WORKFLOW EXAMPLE ===")
    
    # Simulate AI agent workflow
    workflow_steps = [
        {
            "step": 1,
            "action": "get_stock_price_tool",
            "params": {"symbol": "RELIANCE.NS"},
            "purpose": "Get current Reliance stock price for portfolio tracking"
        },
        {
            "step": 2,
            "action": "get_stock_quote_tool",
            "params": {"symbol": "TCS.NS"},
            "purpose": "Get comprehensive TCS stock quote for analysis"
        },
        {
            "step": 3,
            "action": "get_fed_rates_tool",
            "params": {},
            "purpose": "Check Federal Reserve rates for economic analysis"
        },
        {
            "step": 4,
            "action": "get_inflation_data_tool",
            "params": {},
            "purpose": "Analyze inflation trends for investment decisions"
        }
    ]
    
    print("🤖 AI Agent Workflow Simulation:")
    for step in workflow_steps:
        print(f"\n   Step {step['step']}: {step['action']}")
        print(f"   Parameters: {step['params']}")
        print(f"   Purpose: {step['purpose']}")
    
    print(f"\n📊 Analysis Results:")
    print("   • Reliance stock is trading at ₹2450.75 (+1.27%)")
    print("   • TCS stock is trading at ₹3850.25 (+0.85%)")
    print("   • Federal Funds Rate is 5.25%")
    print("   • CPI inflation is 3.1% YoY")
    
    print(f"\n💡 AI Agent Recommendations:")
    print("   • Market sentiment is positive with gains across major indices")
    print("   • Inflation remains elevated but stable")
    print("   • Consider diversifying into defensive sectors given economic uncertainty")
    print("   • Monitor Fed policy for potential rate changes")


async def main():
    """Run all examples"""
    print("🚀 FinanceMCP Usage Examples")
    print("=" * 50)
    
    await example_stock_analysis()
    await example_macroeconomic_analysis()
    await example_comprehensive_market_analysis()
    await example_ai_agent_workflow()
    
    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("\nTo use these tools with an actual AI agent:")
    print("1. Start the FinanceMCP server: python server.py")
    print("2. Configure your AI agent to connect to the MCP server")
    print("3. Use the tool names shown in the examples")
    print("4. Handle the JSON responses as demonstrated")


if __name__ == "__main__":
    asyncio.run(main())
