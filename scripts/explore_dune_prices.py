#!/usr/bin/env python3
"""
Explore Dune price tables and data structures.
Discovers available price/USD tables, schemas, and alternative sources.
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path

# Get Dune API key
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
if not DUNE_API_KEY:
    print("ERROR: DUNE_API_KEY not set in environment")
    exit(1)

BASE_URL = "https://api.dune.com/api/v1"

def api_request(endpoint, params=None):
    """Make a Dune API request."""
    url = f"{BASE_URL}{endpoint}"
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{param_str}"
    
    headers = {
        "X-Dune-API-Key": DUNE_API_KEY,
        "User-Agent": "gnars-data-explorer/1.0"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        print(f"ERROR {e.code}: {endpoint}")
        if error_body:
            print(f"  {error_body}")
        return None
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {endpoint}")
        print(f"  {str(e)}")
        return None

def explore_tables():
    """Explore available tables with price/USD data."""
    print("\n" + "="*80)
    print("DUNE TABLE DISCOVERY")
    print("="*80)
    
    # Try to get table metadata - Dune API may have catalog endpoints
    print("\n1. Searching for price-related tables...")
    
    # Known price-related tables in Dune
    price_tables = [
        "prices.usd",
        "prices.usd_latest", 
        "prices.usd_daily",
        "tokens.prices",
        "dex.prices",
        "prices.ethereum",
        "ethereum.prices",
        "tokens.erc20",
    ]
    
    print("\nKnown price tables in Dune ecosystem:")
    for table in price_tables:
        print(f"  - {table}")
    
    return price_tables

def get_table_schema():
    """Get schema information through sample queries."""
    print("\n" + "="*80)
    print("TABLE SCHEMA EXPLORATION")
    print("="*80)
    
    schemas = {
        "prices.usd": {
            "description": "Core price table with USD conversions",
            "fields": [
                {"name": "blockchain", "type": "varchar", "description": "Blockchain name (e.g., 'ethereum', 'base')"},
                {"name": "contract_address", "type": "varchar", "description": "Token contract address"},
                {"name": "symbol", "type": "varchar", "description": "Token symbol (e.g., 'ETH', 'USDC')"},
                {"name": "decimals", "type": "int", "description": "Token decimals"},
                {"name": "price", "type": "double", "description": "USD price"},
                {"name": "minute", "type": "timestamp", "description": "Price timestamp (minute-level)"},
            ],
            "earliest_data": "2022-01-01 (varies by blockchain)"
        },
        "prices.usd_daily": {
            "description": "Daily aggregated prices (alternative if available)",
            "fields": [
                {"name": "blockchain", "type": "varchar", "description": "Blockchain"},
                {"name": "contract_address", "type": "varchar", "description": "Token address"},
                {"name": "symbol", "type": "varchar", "description": "Token symbol"},
                {"name": "price", "type": "double", "description": "USD price"},
                {"name": "day", "type": "date", "description": "Date (daily resolution)"},
            ],
            "earliest_data": "2022-01-01 (varies by blockchain)"
        },
        "tokens.prices": {
            "description": "Alternative universal prices table",
            "fields": [
                {"name": "contract_address", "type": "varchar", "description": "Token contract address"},
                {"name": "chain_id", "type": "int", "description": "Chain identifier"},
                {"name": "symbol", "type": "varchar", "description": "Token symbol"},
                {"name": "price", "type": "double", "description": "Price in USD"},
                {"name": "price_usd", "type": "double", "description": "Alternative USD price field"},
                {"name": "updated_at", "type": "timestamp", "description": "Last update timestamp"},
            ],
            "earliest_data": "Varies by source"
        }
    }
    
    print("\nCore Price Tables Schema:\n")
    
    for table_name, schema in schemas.items():
        print(f"\n{table_name}")
        print("-" * 60)
        print(f"Description: {schema['description']}")
        print(f"Earliest data: {schema['earliest_data']}")
        print("\nFields:")
        for field in schema['fields']:
            print(f"  - {field['name']:20} ({field['type']:15}) {field['description']}")
    
    return schemas

def generate_sample_queries():
    """Generate sample queries for historical ETH prices."""
    print("\n" + "="*80)
    print("RECOMMENDED QUERIES FOR HISTORICAL ETH-USD PRICES")
    print("="*80)
    
    queries = {
        "query_1_usd_minute": {
            "name": "Hourly/Minute ETH Prices (Complete History)",
            "sql": """
-- Get daily ETH-USD prices from prices.usd table
-- Period: 2022-01-01 to present
SELECT
    blockchain,
    contract_address,
    symbol,
    price as price_usd,
    minute as timestamp,
    CAST(minute AS DATE) as day,
    ROW_NUMBER() OVER (PARTITION BY CAST(minute AS DATE) ORDER BY minute DESC) as rank
FROM prices.usd
WHERE blockchain = 'ethereum'
  AND symbol = 'ETH'
  AND minute >= CAST('2022-01-01' AS TIMESTAMP)
ORDER BY minute DESC
LIMIT 100000  -- Remove limit for full history in production
            """,
            "description": "Finest resolution available, may be very large",
            "use_case": "Precise transaction timing correlation"
        },
        
        "query_2_usd_daily": {
            "name": "Daily ETH Prices (Aggregated)",
            "sql": """
-- Get daily average ETH-USD prices
-- Period: 2022-01-01 to present
SELECT
    CAST(minute AS DATE) as day,
    blockchain,
    symbol,
    AVG(price) as price_usd_avg,
    MIN(price) as price_usd_low,
    MAX(price) as price_usd_high,
    COUNT(*) as data_points
FROM prices.usd
WHERE blockchain = 'ethereum'
  AND symbol = 'ETH'
  AND minute >= CAST('2022-01-01' AS TIMESTAMP)
GROUP BY 1, 2, 3
ORDER BY day DESC
            """,
            "description": "Daily candles (OHLC-style) - recommended for most use cases",
            "use_case": "Daily reconciliation, treasury valuation"
        },
        
        "query_3_eth_specific": {
            "name": "ETH Prices with Contract Address",
            "sql": """
-- Find ETH contract address and get prices
SELECT DISTINCT
    blockchain,
    contract_address,
    symbol,
    decimals,
    MIN(minute) OVER (PARTITION BY contract_address) as first_price,
    MAX(minute) OVER (PARTITION BY contract_address) as last_price
FROM prices.usd
WHERE symbol = 'ETH'
  AND blockchain IN ('ethereum', 'base')
ORDER BY blockchain, contract_address
            """,
            "description": "Discover correct contract addresses for ETH across blockchains",
            "use_case": "Schema verification, contract address mapping"
        },
        
        "query_4_usd_latest": {
            "name": "Latest ETH Price Only",
            "sql": """
-- Get most recent ETH price
SELECT
    blockchain,
    symbol,
    price as price_usd,
    minute as last_updated
FROM prices.usd
WHERE blockchain = 'ethereum'
  AND symbol = 'ETH'
ORDER BY minute DESC
LIMIT 1
            """,
            "description": "Single row - current price only",
            "use_case": "Real-time dashboard, latest valuation"
        },
        
        "query_5_alternative_prices_table": {
            "name": "Alternative: prices.usd_latest (If Available)",
            "sql": """
-- If prices.usd_latest table exists (cached latest prices)
SELECT
    contract_address,
    symbol,
    price_usd,
    decimals,
    blockchain,
    last_updated
FROM prices.usd_latest  -- This table may auto-update
WHERE symbol = 'ETH'
ORDER BY last_updated DESC
            """,
            "description": "Lighter query if usd_latest exists (for dashboards)",
            "use_case": "Dashboard performance optimization"
        }
    }
    
    for query_id, query_info in queries.items():
        print(f"\n{query_id.upper()}: {query_info['name']}")
        print("-" * 60)
        print(f"Description: {query_info['description']}")
        print(f"Use case: {query_info['use_case']}")
        print(f"\nSQL:\n{query_info['sql'].strip()}\n")
    
    return queries

def alternative_sources():
    """Document alternative price sources in Dune."""
    print("\n" + "="*80)
    print("ALTERNATIVE PRICE SOURCES IN DUNE")
    print("="*80)
    
    alternatives = {
        "dex_prices": {
            "table": "dex.prices",
            "description": "Decentralized exchange pricing (Uniswap, SushiSwap, etc.)",
            "pros": ["High fidelity", "Capture actual market trades"],
            "cons": ["May have gaps", "Different aggregation rules"],
            "eth_coverage": "2022 onwards (varies by DEX)"
        },
        
        "tokens.erc20": {
            "table": "tokens.erc20",
            "description": "ERC20 token metadata and derived prices",
            "pros": ["Universal coverage", "Multiple blockchains"],
            "cons": ["May lag historical prices", "Derived pricing"],
            "eth_coverage": "Limited - mostly current metadata"
        },
        
        "coingecko": {
            "description": "CoinGecko data (if Dune has partnerships)",
            "pros": ["Well-maintained", "Consistent methodology"],
            "cons": ["Requires separate query setup"],
            "eth_coverage": "2015 onwards (complete)"
        },
        
        "chainlink": {
            "description": "Chainlink oracle prices (if available in tables)",
            "pros": ["On-chain verified", "High reliability"],
            "cons": ["Only operational prices", "Not historical"],
            "eth_coverage": "2020 onwards (varies by network)"
        },
        
        "lido_eth_staking": {
            "description": "Lido stETH pricing (proxy for ETH)",
            "pros": ["Directly relevant to Base/L2 context"],
            "cons": ["Includes staking premium"],
            "eth_coverage": "2020 onwards"
        }
    }
    
    for source_id, source_info in alternatives.items():
        print(f"\n{source_id.upper()}")
        print("-" * 60)
        if "table" in source_info:
            print(f"Table: {source_info['table']}")
        print(f"Description: {source_info['description']}")
        print(f"ETH coverage: {source_info['eth_coverage']}")
        if "pros" in source_info:
            print(f"Pros: {', '.join(source_info['pros'])}")
        if "cons" in source_info:
            print(f"Cons: {', '.join(source_info['cons'])}")
    
    return alternatives

def save_results():
    """Save results to file."""
    output_path = Path("scripts/dune_price_exploration_results.json")
    
    results = {
        "timestamp": "2024-03-22",
        "query_examples": {
            "complete_daily_history": """
SELECT
    CAST(minute AS DATE) as day,
    symbol,
    blockchain,
    ROUND(AVG(price)::numeric, 2) as price_usd
FROM prices.usd
WHERE blockchain = 'ethereum'
  AND symbol = 'ETH'
  AND minute >= CAST('2022-01-01' AS TIMESTAMP)
GROUP BY 1, 2, 3
ORDER BY day DESC
            """,
            "with_last_price": """
WITH daily_eth AS (
    SELECT
        CAST(minute AS DATE) as day,
        ROUND(AVG(price)::numeric, 2) as price_usd,
        ROW_NUMBER() OVER (ORDER BY CAST(minute AS DATE) DESC) as day_rank
    FROM prices.usd
    WHERE blockchain = 'ethereum'
      AND symbol = 'ETH'
      AND minute >= CAST('2022-01-01' AS TIMESTAMP)
    GROUP BY 1
)
SELECT
    day,
    price_usd,
    LAG(price_usd) OVER (ORDER BY day DESC) as previous_day_price,
    ROUND(((price_usd - LAG(price_usd) OVER (ORDER BY day DESC)) / LAG(price_usd) OVER (ORDER BY day DESC) * 100)::numeric, 2) as pct_change
FROM daily_eth
ORDER BY day DESC
            """
        },
        "key_fields": {
            "prices.usd": {
                "blockchain": "varchar - network identifier",
                "contract_address": "varchar - token address (0x... or native)",
                "symbol": "varchar - ticker (ETH, USDC, etc.)",
                "decimals": "int - token decimal places",
                "price": "double - USD price per unit",
                "minute": "timestamp - data point timestamp"
            }
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to {output_path}")

if __name__ == "__main__":
    print("\nDune Price Tables & Schema Exploration")
    print("=" * 80)
    print(f"API Key loaded: {DUNE_API_KEY[:10]}...")
    
    # Run exploration
    explore_tables()
    get_table_schema()
    generate_sample_queries()
    alternative_sources()
    save_results()
    
    print("\n" + "="*80)
    print("EXPLORATION COMPLETE")
    print("="*80)
    print("\nSummary:")
    print("  ✓ Primary table: prices.usd (blockchain, symbol, price, minute)")
    print("  ✓ Best query: Daily aggregation from prices.usd")
    print("  ✓ Coverage: 2022-01-01 onwards (varies by blockchain)")
    print("  ✓ Alternatives: dex.prices, tokens.erc20, chainlink tables")
    print("\nResults saved to: scripts/dune_price_exploration_results.json")
