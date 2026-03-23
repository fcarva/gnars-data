# Dune ETH-USD Prices — Quick Reference

## Exploration Complete ✓

### Primary Table: `prices.usd`

```
Field              Type              Description
────────────────────────────────────────────────────────────
blockchain         varchar           'ethereum', 'base', etc.
contract_address   varchar           0x0000... for native ETH
symbol             varchar           'ETH', 'USDC', 'USDT'
decimals           int               18 for ETH
price              double precision  USD price per unit
minute             timestamp         Data point timestamp
```

---

## Production Query for Gnars

```sql
SELECT
    CAST(minute AS DATE) as day,
    blockchain,
    symbol,
    ROUND(AVG(price)::numeric, 2) as price_usd,
    MIN(price) as low_price,
    MAX(price) as high_price
FROM prices.usd
WHERE blockchain = 'ethereum'
  AND symbol = 'ETH'
  AND minute >= CAST('2022-01-01' AS TIMESTAMP)
GROUP BY 1, 2, 3
ORDER BY day DESC;
```

**Expected output:** ~900 rows (one per day 2022–present)

---

## Coverage & Availability

| Blockchain | Start Date | Status | Notes |
|-----------|-----------|--------|-------|
| Ethereum  | 2022-01-01 | ✓ Complete | Highest volume, most reliable |
| Base      | 2023-08-01 | ✓ Complete | Since mainnet launch |
| Polygon   | 2022-01-01 | ✓ Available | Full history |

---

## Alternative Price Sources

| Table | Type | Best For | Range |
|-------|------|----------|-------|
| `dex.prices` | DEX trades | Market validation | Varies |
| `tokens.prices` | Cross-chain | Token lookups | Varies |
| `chainlink` | Oracle | On-chain prices | 2020+ |
| `coingecko` | Historical | Complete history | 2015+ |

---

## For gnars-data Pipeline

### Use in:
- `scripts/sync_eth_prices.py` (new) — daily price fetching
- `scripts/reconcile_treasury.py` — treasury valuation
- `scripts/derive_funding_analysis.py` — historical analysis

### Store as:
- `data/eth_prices_daily.json` — daily OHLC for GUARs treasury

### Schema:
```json
{
  "day": "2024-03-22",
  "blockchain": "ethereum",
  "symbol": "ETH",
  "price_usd": 3284.51,
  "low_price": 3261.23,
  "high_price": 3299.87,
  "data_points": 1440
}
```

---

## Validation Checklist

- [ ] Query returns data for all dates 2022-01-01 to today
- [ ] No null prices in results
- [ ] Daily prices in reasonable range (e.g., $1,000–$4,000)
- [ ] No duplicate day entries  
- [ ] Execution time < 10 seconds
- [ ] Field names match schema
- [ ] All timestamps are UTC

---

**Full documentation:** [dune_prices_schema_guide.md](dune_prices_schema_guide.md)  
**Exploration script:** `scripts/explore_dune_prices.py`  
**Generated:** 2024-03-22
