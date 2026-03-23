# Dune Queries Configuration Guide

## Status Atual

Auctions estão configuradas como `null` em `data/sources.json`:
```json
{
  "gnars_auctions_base": null,
  "gnars_auctions_ethereum": null,
  "treasury_outflows_base": null
}
```

## Como Configurar

### Pré-requisitos
- Conta Dune Analytics (https://dune.com/)
- API Key em `.env` → `DUNE_API_KEY`
- Acesso ao dashboard Gnars: https://dune.com/0xsatori/gnarsv2

### Step 1: Criar Query para Gnars Auctions (Base)

**URL**: https://dune.com/queries/new

**SQL Template**:
```sql
-- Gnars Auctions - Base Network
SELECT
  block_time,
  auction_id,
  gnars_id,
  settled_at,
  winner,
  amount_eth,
  amount_usd,
  tx_hash,
  block_number
FROM
  (
    SELECT
      l.block_time,
      CAST(decoded_log.auction_id AS INT) AS auction_id,
      CAST(decoded_log.gnars_id AS INT) AS gnars_id,
      l.tx_hash,
      CAST(decoded_log.bidder AS STRING) AS winner,
      CAST(decoded_log.amount AS DOUBLE) / 1e18 AS amount_eth,
      (CAST(decoded_log.amount AS DOUBLE) / 1e18) * p.price AS amount_usd,
      l.block_time AS settled_at,
      l.block_number
    FROM
      base.logs l
      INNER JOIN base.prices p 
        ON DATE_TRUNC('minute', l.block_time) = p.minute
        AND p.blockchain = 'base'
        AND p.symbol = 'ETH'
      CROSS JOIN LATERAL FLATTEN(l.topics) AS topics
    WHERE
      l.contract_address = LOWER('0x494Eaa55ECF6310658B8fC004b0888DCDB698097f')
      AND l.topic0 = 'AuctionSettled(uint256,uint256,address,uint256)'
    ORDER BY
      l.block_time DESC
  )
ORDER BY
  settled_at DESC
```

**Save as**: "Gnars Auctions - Base"  
**Note the Query ID** (e.g., 1234567)

### Step 2: Criar Query para Gnars Auctions (Ethereum)

**SQL Template** (similar, change to Ethereum):
```sql
-- Gnars Auctions - Ethereum Network
SELECT
  block_time,
  auction_id,
  gnars_id,
  settled_at,
  winner,
  amount_eth,
  amount_usd,
  tx_hash,
  block_number
FROM
  (
    SELECT
      l.block_time,
      CAST(decoded_log.auction_id AS INT) AS auction_id,
      CAST(decoded_log.gnars_id AS INT) AS gnars_id,
      l.tx_hash,
      CAST(decoded_log.bidder AS STRING) AS winner,
      CAST(decoded_log.amount AS DOUBLE) / 1e18 AS amount_eth,
      (CAST(decoded_log.amount AS DOUBLE) / 1e18) * p.price AS amount_usd,
      l.block_time AS settled_at,
      l.block_number
    FROM
      ethereum.logs l
      INNER JOIN ethereum.prices p 
        ON DATE_TRUNC('minute', l.block_time) = p.minute
        AND p.blockchain = 'ethereum'
        AND p.symbol = 'ETH'
      CROSS JOIN LATERAL FLATTEN(l.topics) AS topics
    WHERE
      l.contract_address = LOWER('0x...')  -- Ethereum auction house address
      AND l.topic0 = 'AuctionSettled(uint256,uint256,address,uint256)'
    ORDER BY
      l.block_time DESC
  )
ORDER BY
  settled_at DESC
```

**Save as**: "Gnars Auctions - Ethereum"  
**Note the Query ID**

### Step 3: Update Configuration

Edit `data/sources.json`:
```json
{
  "dune_queries": {
    "gnars_auctions_base": "1234567",      // Replace with actual ID
    "gnars_auctions_ethereum": "1234568"   // Replace with actual ID
  }
}
```

### Step 4: Update fetch_dune_data.py

The script already has mapping for `fetch_dune_data.py`. Query IDs will be auto-fetched on next `refresh_all.py` run.

```bash
python scripts/refresh_all.py --incremental
```

## Expected Output

After configuration, the pipeline will generate:
- `data/auctions_base_individual.json` - Individual auction records
- `data/auctions_ethereum_individual.json` - Historical auctions
- Enhanced `dao_metrics.json` with full auction breakdown

## Notes

- Queries are **append-only** — use `UNION` for historical data
- ETH prices come from `blockchain.prices` table (standard Dune)
- Winner address may need ENS resolution for display
- Treasury opening balance can be verified against Dune historical balances
