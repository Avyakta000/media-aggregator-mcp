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
    
    # Get Apple stock quote
    apple_quote = {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "current_price": 150.25,
        "previous_close": 148.10,
        "change": 2.15,
        "change_percent": 1.45,
        "volume": 1234567,
        "market_cap": 2500000000000,
        "pe_ratio": 25.5,
        "dividend_yield": 0.65,
        "sector": "Technology",
        "industry": "Consumer Electronics"
    }
    
    print(f"📈 {apple_quote['company_name']} ({apple_quote['symbol']})")
    print(f"   Current Price: ${apple_quote['current_price']}")
    print(f"   Change: ${apple_quote['change']} ({apple_quote['change_percent']}%)")
    print(f"   Market Cap: ${apple_quote['market_cap']:,}")
    print(f"   P/E Ratio: {apple_quote['pe_ratio']}")
    print(f"   Dividend Yield: {apple_quote['dividend_yield']}%")
    
    # Get historical data
    historical_data = {
        "symbol": "AAPL",
        "period": "1mo",
        "interval": "1d",
        "data": [
            {"date": "2024-01-15", "close": 150.25, "volume": 1234567},
            {"date": "2024-01-14", "close": 148.10, "volume": 1154321},
            {"date": "2024-01-13", "close": 147.85, "volume": 1123456}
        ]
    }
    
    print(f"\n📊 Historical Data (1 month):")
    for point in historical_data['data'][:3]:
        print(f"   {point['date']}: ${point['close']} (Volume: {point['volume']:,})")


async def example_forex_analysis():
    """Example: Foreign exchange analysis"""
    print("\n=== FOREX ANALYSIS EXAMPLE ===")
    
    # Get USD/EUR exchange rate
    usd_eur_rate = {
        "from_currency": "USD",
        "to_currency": "EUR",
        "rate": 0.85,
        "inverse_rate": 1.18,
        "change": 0.002,
        "change_percent": 0.24,
        "high": 0.852,
        "low": 0.843,
        "timestamp": "2024-01-15T16:00:00Z"
    }
    
    print(f"💱 {usd_eur_rate['from_currency']}/{usd_eur_rate['to_currency']} Exchange Rate")
    print(f"   Current Rate: {usd_eur_rate['rate']}")
    print(f"   Change: {usd_eur_rate['change']} ({usd_eur_rate['change_percent']}%)")
    print(f"   Day Range: {usd_eur_rate['low']} - {usd_eur_rate['high']}")
    
    # Currency conversion example
    conversion = {
        "amount": 1000,
        "from_currency": "USD",
        "to_currency": "EUR",
        "rate": 0.85,
        "converted_amount": 850.0
    }
    
    print(f"\n💰 Currency Conversion:")
    print(f"   {conversion['amount']} {conversion['from_currency']} = {conversion['converted_amount']} {conversion['to_currency']}")


async def example_crypto_analysis():
    """Example: Cryptocurrency market analysis"""
    print("\n=== CRYPTOCURRENCY ANALYSIS EXAMPLE ===")
    
    # Get Bitcoin market data
    btc_data = {
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
    
    print(f"₿ Bitcoin ({btc_data['symbol']}) Market Data")
    print(f"   Current Price: ${btc_data['market_data']['current_price']:,}")
    print(f"   Market Cap: ${btc_data['market_data']['market_cap']:,}")
    print(f"   Market Cap Rank: #{btc_data['market_data']['market_cap_rank']}")
    print(f"   24h Volume: ${btc_data['market_data']['volume_24h']:,}")
    print(f"   24h Change: ${btc_data['price_change']['change_24h']} ({btc_data['price_change']['change_percent_24h']}%)")
    print(f"   7d Change: ${btc_data['price_change']['change_7d']} ({btc_data['price_change']['change_percent_7d']}%)")
    print(f"   Circulating Supply: {btc_data['market_data']['circulating_supply']:,} BTC")


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
            "sp500": {"symbol": "^GSPC", "price": 4800.50, "change": 25.30, "change_percent": 0.53},
            "nasdaq": {"symbol": "^IXIC", "price": 15200.75, "change": 45.20, "change_percent": 0.30},
            "dow": {"symbol": "^DJI", "price": 37500.25, "change": 150.75, "change_percent": 0.40}
        },
        "forex_markets": {
            "usd_eur": {"rate": 0.85, "change": 0.002, "change_percent": 0.24},
            "usd_gbp": {"rate": 0.78, "change": -0.001, "change_percent": -0.13},
            "usd_jpy": {"rate": 148.50, "change": 0.75, "change_percent": 0.51}
        },
        "crypto_markets": {
            "btc": {"price": 45000.50, "change": 1250.25, "change_percent": 2.86},
            "eth": {"price": 2800.75, "change": 85.50, "change_percent": 3.15},
            "market_cap_total": 1850000000000
        },
        "macro_indicators": {
            "fed_funds_rate": 5.25,
            "inflation_cpi": 3.1,
            "unemployment_rate": 3.7,
            "gdp_growth": 2.1
        }
    }
    
    print(f"🌍 Global Market Summary - {market_summary['timestamp']}")
    
    print(f"\n📈 Equity Markets:")
    for index, data in market_summary['equity_markets'].items():
        print(f"   {index.upper()}: ${data['price']:,} ({data['change']:+} / {data['change_percent']:+.2f}%)")
    
    print(f"\n💱 Forex Markets:")
    for pair, data in market_summary['forex_markets'].items():
        print(f"   {pair.upper()}: {data['rate']} ({data['change']:+} / {data['change_percent']:+.2f}%)")
    
    print(f"\n₿ Cryptocurrency Markets:")
    for crypto, data in market_summary['crypto_markets'].items():
        if crypto != 'market_cap_total':
            print(f"   {crypto.upper()}: ${data['price']:,} ({data['change']:+} / {data['change_percent']:+.2f}%)")
    print(f"   Total Market Cap: ${market_summary['crypto_markets']['market_cap_total']:,}")
    
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
            "params": {"symbol": "AAPL"},
            "purpose": "Get current Apple stock price for portfolio tracking"
        },
        {
            "step": 2,
            "action": "get_forex_rate_tool",
            "params": {"from_currency": "USD", "to_currency": "EUR"},
            "purpose": "Check USD/EUR rate for international investment analysis"
        },
        {
            "step": 3,
            "action": "get_crypto_price_tool",
            "params": {"symbol": "BTC", "market": "USD"},
            "purpose": "Monitor Bitcoin price for crypto portfolio"
        },
        {
            "step": 4,
            "action": "get_fed_rates_tool",
            "params": {},
            "purpose": "Check Federal Reserve rates for economic analysis"
        },
        {
            "step": 5,
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
    print("   • Apple stock is trading at $150.25 (+1.45%)")
    print("   • USD/EUR exchange rate is 0.85 (+0.24%)")
    print("   • Bitcoin is at $45,000 (+2.86%)")
    print("   • Federal Funds Rate is 5.25%")
    print("   • CPI inflation is 3.1% YoY")
    
    print(f"\n💡 AI Agent Recommendations:")
    print("   • Market sentiment is positive with gains across major indices")
    print("   • Inflation remains elevated but stable")
    print("   • Consider diversifying into international markets given USD strength")
    print("   • Monitor Fed policy for potential rate changes")


async def main():
    """Run all examples"""
    print("🚀 FinanceMCP Usage Examples")
    print("=" * 50)
    
    await example_stock_analysis()
    await example_forex_analysis()
    await example_crypto_analysis()
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
