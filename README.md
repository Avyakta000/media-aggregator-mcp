# FinanceMCP

A production-ready MCP (Model Context Protocol) server for comprehensive financial data using FastMCP. Provides real-time access to Indian stock market data and macroeconomic indicators.

## Features

### 📈 Indian Stock Market Data
- **Real-time Indian stock prices** from Yahoo Finance (NSE & BSE)
- **Comprehensive stock quotes** with detailed financial metrics
- **Historical price data** with customizable timeframes
- **Fundamental analysis** including P/E ratios, market cap, dividends
- **Stock search** by Indian company name or symbol (prioritizes Indian stocks)
- **Smart symbol handling**: Pass just stock names (e.g., "RELIANCE") and automatically try NSE (.NS) first, then BSE (.BO)
- **NSE and BSE support** with proper exchange suffixes (.NS, .BO)
- **Comprehensive stock analysis** with technical indicators and research-style reports

### 📊 Macroeconomic Indicators
- **Federal Reserve rates** and monetary policy data
- **Inflation metrics** (CPI, PCE, Core CPI)
- **GDP data** (Real and Nominal)
- **Unemployment statistics** and labor market data
- **Economic indicators** from FRED (Federal Reserve Economic Data)

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd finance-mcp

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys and ScaleKit settings
nano .env
```

**Required API Keys:**
- **Alpha Vantage**: Free API key for stock data
- **FRED**: Free API key for macroeconomic data

**Required ScaleKit Settings:**
- **ScaleKit Environment URL**: Your ScaleKit environment URL
- **ScaleKit Client ID**: Your ScaleKit client ID
- **ScaleKit Client Secret**: Your ScaleKit client secret
- **ScaleKit Audience Name**: Your ScaleKit audience name

For detailed ScaleKit setup instructions, see [SCALEKIT_SETUP.md](SCALEKIT_SETUP.md).

### 3. Run the Server

```bash
# Start the server with ScaleKit authentication
python server.py
```

The server will be available at `http://localhost:3000` (or the port specified in your .env file)

**Note**: The server now requires ScaleKit authentication. All requests (except well-known endpoints) must include a valid Bearer token in the Authorization header.

## API Tools

### Indian Stock Market Tools

| Tool | Description | Example |
|------|-------------|---------|
| `get_stock_price_tool` | Get current Indian stock price | `get_stock_price_tool("RELIANCE")` or `get_stock_price_tool("RELIANCE.NS")` |
| `get_stock_quote_tool` | Get comprehensive stock quote | `get_stock_quote_tool("TCS")` or `get_stock_quote_tool("TCS.NS")` |
| `get_stock_history_tool` | Get historical price data | `get_stock_history_tool("HDFCBANK", period="1mo")` or `get_stock_history_tool("HDFCBANK.NS", period="1mo")` |
| `get_stock_fundamentals_tool` | Get fundamental data | `get_stock_fundamentals_tool("INFY")` or `get_stock_fundamentals_tool("INFY.NS")` |
| `search_stocks_tool` | Search for Indian stocks | `search_stocks_tool("Reliance", limit=5)` |
| `analyze_stock_tool` | Get comprehensive stock analysis | `analyze_stock_tool("RELIANCE")` |

### Macroeconomic Tools

| Tool | Description | Example |
|------|-------------|---------|
| `get_economic_indicator_tool` | Get economic indicator | `get_economic_indicator_tool("GDP")` |
| `get_fed_rates_tool` | Get Federal Reserve rates | `get_fed_rates_tool()` |
| `get_inflation_data_tool` | Get inflation data | `get_inflation_data_tool()` |
| `get_gdp_data_tool` | Get GDP data | `get_gdp_data_tool()` |
| `get_unemployment_data_tool` | Get unemployment data | `get_unemployment_data_tool()` |
| `get_popular_indicators_tool` | Get popular indicators | `get_popular_indicators_tool()` |

## Authentication

This server uses ScaleKit for OAuth 2.0 authentication. All requests (except well-known endpoints) require a valid Bearer token.

### Public Endpoints
- `GET /.well-known/oauth-protected-resource/mcp` - OAuth 2.0 discovery endpoint (no authentication required)

### Protected Endpoints
All MCP endpoints require authentication:
- Include `Authorization: Bearer <your_token>` header in requests
- Invalid or missing tokens return 401 Unauthorized

### Testing Authentication
```bash
# Test well-known endpoint (no auth required)
curl http://localhost:3000/.well-known/oauth-protected-resource/mcp

# Test protected endpoint (auth required)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/mcp
```

For detailed authentication setup, see [SCALEKIT_SETUP.md](SCALEKIT_SETUP.md).

## Resources

The server provides RESTful resources for easy data access:

- `finance://status` - Server status
- `finance://indicators` - Popular economic indicators
- `finance://stock/{symbol}` - Stock quote
- `finance://macro/fed-rates` - Federal Reserve rates
- `finance://macro/inflation` - Inflation data
- `finance://macro/gdp` - GDP data

## Usage Examples

### AI Agent Integration

```python
# Example: Get Reliance stock price (with automatic suffix handling)
result = await get_stock_price_tool("RELIANCE")  # Will try RELIANCE.NS first, then RELIANCE.BO
print(f"Reliance stock price: ₹{result['price']}")

# Example: Get TCS stock with explicit NSE suffix
result = await get_stock_price_tool("TCS.NS")
print(f"TCS stock price: ₹{result['price']}")

# Example: Get comprehensive stock analysis
result = await analyze_stock_tool("RELIANCE")
print(f"Analysis: {result['summary']['overall_view']}")

# Example: Get Federal Reserve rates
result = await get_fed_rates_tool()
print(f"Federal Funds Rate: {result['rates']['federal_funds_rate']['current']}%")
```

### Market Analysis

```python
# Get comprehensive market analysis
stock_data = await get_stock_quote_tool("RELIANCE")  # Will try RELIANCE.NS first, then RELIANCE.BO
macro_data = await get_inflation_data_tool()

# Analyze market conditions
print(f"Reliance: ₹{stock_data['current_price']}")
print(f"Inflation (CPI): {macro_data['inflation_indicators']['cpi_all_urban']['year_over_year_change']}%")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_NAME` | Server name | `FinanceMCP` |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Required |
| `FRED_API_KEY` | FRED API key | Required |
| `AUTHKIT_DOMAIN` | AuthKit domain (optional) | None |
| `BASE_URL` | Base URL (optional) | None |
| `DEFAULT_CURRENCY` | Default currency | `INR` |
| `DEFAULT_MARKET` | Default market | `IN` |
| `DEFAULT_TIMEFRAME` | Default timeframe | `1d` |
| `REQUESTS_PER_MINUTE` | Rate limiting | `60` |
| `CACHE_TTL_SECONDS` | Cache TTL | `300` |

### API Rate Limits

- **Alpha Vantage**: 5 requests per minute (free tier)
- **FRED**: 120 requests per minute (free tier)
- **Yahoo Finance**: No rate limits (public data)

## Architecture

```
FinanceMCP/
├── server.py              # Main server file
├── settings.py            # Configuration settings
├── requirements.txt       # Python dependencies
├── tools/                 # Financial tools modules
│   ├── __init__.py
│   ├── stock_tools.py     # Stock market tools
│   └── macro_tools.py     # Macroeconomic tools
├── env.example           # Environment template
└── README.md            # This file
```

## Data Sources

- **Yahoo Finance**: Primary source for Indian stock data (NSE & BSE)
- **Alpha Vantage**: Alternative source for stock data
- **FRED**: Federal Reserve Economic Data for macroeconomic indicators

## Error Handling

The server includes comprehensive error handling:
- **Retry logic** with exponential backoff
- **Rate limiting** to respect API limits
- **Graceful degradation** when APIs are unavailable
- **Detailed error messages** for debugging

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "server.py"]
```

### Environment Setup

```bash
# Production environment variables
export MCP_SERVER_NAME=FinanceMCP
export ALPHA_VANTAGE_API_KEY=your_production_key
export FRED_API_KEY=your_production_key
export REQUESTS_PER_MINUTE=100
export CACHE_TTL_SECONDS=600
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the example configurations

## Roadmap

- [ ] Add more data sources
- [ ] Implement caching layer
- [ ] Add WebSocket support for real-time data
- [ ] Create dashboard interface
- [ ] Add more technical indicators
- [ ] Implement portfolio tracking
- [ ] Add news sentiment analysis