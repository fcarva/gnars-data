-- Gnars DAO Dune dashboard queries
-- Base addresses from data/contracts.json
-- Base NFT:           0x880fb3cf5c6cc2d7dfc13a993e839a9411200c17
-- Base Auction House: 0x494eaa55ecf6310658b8fc004b0888dcb698097f
-- Base Governor:      0x3dd4e53a232b7b715c9ae455f4e732465ed71b4c
-- Base Treasury:      0x72ad986ebac0246d2b3c565ab2a1ce3a14ce6f88
-- Base USDC:          0x833589fcd6edb6e08f4c7c32d4f71b54bda02913

-- Event topic0 hashes:
-- AuctionSettled(uint256,address,uint256)
--   0xc9f72b276a388619c6d185d146697036241880c36654b1a3ffdad07c24038d99
-- ProposalExecuted(uint256)
--   0x712ae1383f79ac853f8d882153778e0260ef8f03b504e2866e0593e04d2b291f
-- VoteCast(address,uint256,uint8,uint256,string)
--   0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4

/* -------------------------------------------------------------------------- */
/* QUERY 1: gnars-treasury-balance-over-time                                  */
/* -------------------------------------------------------------------------- */
WITH monthly_components AS (
    SELECT
        DATE_TRUNC('month', block_time) AS month,
        SUM(BYTEARRAY_TO_UINT256(SUBSTR(data, 65, 32)) / 1e18) AS auction_eth_in,
        CAST(0 AS DOUBLE) AS usdc_out,
        CAST(0 AS DOUBLE) AS eth_out
    FROM base.logs
    WHERE contract_address = 0x494eaa55ecf6310658b8fc004b0888dcb698097f
      AND topic0 = 0xc9f72b276a388619c6d185d146697036241880c36654b1a3ffdad07c24038d99
      AND block_time >= TIMESTAMP '2023-01-01'
    GROUP BY 1

    UNION ALL

    SELECT
        DATE_TRUNC('month', evt_block_time) AS month,
        CAST(0 AS DOUBLE) AS auction_eth_in,
        SUM(CAST(value AS DOUBLE) / 1e6) AS usdc_out,
        CAST(0 AS DOUBLE) AS eth_out
    FROM base.erc20_evt_Transfer
    WHERE contract_address = 0x833589fcd6edb6e08f4c7c32d4f71b54bda02913
      AND "from" = 0x72ad986ebac0246d2b3c565ab2a1ce3a14ce6f88
      AND evt_block_time >= TIMESTAMP '2023-01-01'
    GROUP BY 1

    UNION ALL

    SELECT
        DATE_TRUNC('month', block_time) AS month,
        CAST(0 AS DOUBLE) AS auction_eth_in,
        CAST(0 AS DOUBLE) AS usdc_out,
        SUM(CAST(value AS DOUBLE) / 1e18) AS eth_out
    FROM base.traces
    WHERE "from" = 0x72ad986ebac0246d2b3c565ab2a1ce3a14ce6f88
      AND success = true
      AND value > 0
      AND block_time >= TIMESTAMP '2023-01-01'
    GROUP BY 1
)
SELECT
    month,
    ROUND(SUM(auction_eth_in), 6) AS auction_eth_in,
    ROUND(SUM(usdc_out), 2) AS usdc_out,
    ROUND(SUM(eth_out), 6) AS eth_out
FROM monthly_components
GROUP BY 1
ORDER BY 1;

/* -------------------------------------------------------------------------- */
/* QUERY 2: gnars-auction-revenue-all-time                                    */
/* -------------------------------------------------------------------------- */
WITH settlements AS (
    SELECT
        block_time,
        tx_hash,
        BYTEARRAY_TO_UINT256(SUBSTR(data, 65, 32)) / 1e18 AS eth_amount,
        '0x' || TO_HEX(SUBSTR(data, 13, 20)) AS winner
    FROM base.logs
    WHERE contract_address = 0x494eaa55ecf6310658b8fc004b0888dcb698097f
      AND topic0 = 0xc9f72b276a388619c6d185d146697036241880c36654b1a3ffdad07c24038d99
),
with_price AS (
    SELECT
        s.block_time,
        s.tx_hash,
        s.eth_amount,
        s.winner,
        p.price AS eth_usd_price,
        s.eth_amount * p.price AS usd_value
    FROM settlements s
    LEFT JOIN prices.usd p
      ON p.blockchain = 'base'
     AND p.contract_address = 0x4200000000000000000000000000000000000006
     AND p.minute = DATE_TRUNC('minute', s.block_time)
)
SELECT
    DATE_TRUNC('month', block_time) AS month,
    COUNT(*) AS auction_count,
    ROUND(SUM(eth_amount), 4) AS total_eth,
    ROUND(AVG(eth_usd_price), 2) AS avg_eth_price,
    ROUND(SUM(usd_value), 2) AS total_usd
FROM with_price
GROUP BY 1
ORDER BY 1;

/* -------------------------------------------------------------------------- */
/* QUERY 3: gnars-proposal-spend-by-category                                  */
/* -------------------------------------------------------------------------- */
-- Category mapping should be merged in pipeline using data/proposal_tags.json
-- joined by proposal_id (Dune output) -> proposal_number/proposal_key (pipeline).
WITH
usdc_transfers AS (
    SELECT
        evt_block_number AS block_number,
        evt_block_time AS block_time,
        evt_tx_hash AS tx_hash,
        "to" AS recipient,
        CAST(value AS DOUBLE) / 1e6 AS usdc_amount
    FROM base.erc20_evt_Transfer
    WHERE contract_address = 0x833589fcd6edb6e08f4c7c32d4f71b54bda02913
      AND "from" = 0x72ad986ebac0246d2b3c565ab2a1ce3a14ce6f88
),
governor_logs AS (
    SELECT
        block_number,
        block_time,
        tx_hash,
        TRY(BYTEARRAY_TO_UINT256(topic1)) AS proposal_id
    FROM base.logs
    WHERE contract_address = 0x3dd4e53a232b7b715c9ae455f4e732465ed71b4c
),
proposal_by_tx AS (
    SELECT
        tx_hash,
        MAX(proposal_id) AS proposal_id
    FROM governor_logs
    WHERE proposal_id IS NOT NULL
      AND proposal_id BETWEEN 1 AND 1000000
    GROUP BY 1
),
proposal_by_block AS (
    SELECT
        block_number,
        MAX(proposal_id) AS proposal_id
    FROM governor_logs
    WHERE proposal_id IS NOT NULL
      AND proposal_id BETWEEN 1 AND 1000000
    GROUP BY 1
)
SELECT
    COALESCE(pbt.proposal_id, pbb.proposal_id) AS proposal_id,
    ut.block_time,
    ut.recipient,
    ut.usdc_amount,
    ut.tx_hash,
    CASE
        WHEN pbt.proposal_id IS NOT NULL THEN 'tx_hash'
        WHEN pbb.proposal_id IS NOT NULL THEN 'block_number'
        ELSE 'unmatched'
    END AS match_source
FROM usdc_transfers ut
LEFT JOIN proposal_by_tx pbt
    ON pbt.tx_hash = ut.tx_hash
LEFT JOIN proposal_by_block pbb
    ON pbb.block_number = ut.block_number
ORDER BY ut.block_time DESC;

/* -------------------------------------------------------------------------- */
/* QUERY 4: gnars-holders-over-time                                           */
/* -------------------------------------------------------------------------- */
WITH holder_deltas AS (
    SELECT DATE_TRUNC('month', evt_block_time) AS month, "to" AS holder, 1 AS delta
    FROM base.erc721_evt_Transfer
    WHERE contract_address = 0x880fb3cf5c6cc2d7dfc13a993e839a9411200c17
      AND "to" != 0x0000000000000000000000000000000000000000
    UNION ALL
    SELECT DATE_TRUNC('month', evt_block_time) AS month, "from" AS holder, -1 AS delta
    FROM base.erc721_evt_Transfer
    WHERE contract_address = 0x880fb3cf5c6cc2d7dfc13a993e839a9411200c17
      AND "from" != 0x0000000000000000000000000000000000000000
),
monthly AS (
    SELECT
        month,
        COUNT(DISTINCT CASE WHEN delta = 1 THEN holder END) AS new_holders,
        COUNT(DISTINCT CASE WHEN delta = -1 THEN holder END) AS sellers,
        SUM(delta) AS net_change
    FROM holder_deltas
    GROUP BY 1
)
SELECT
    month,
    new_holders,
    sellers,
    net_change,
    SUM(net_change) OVER (ORDER BY month) AS holders_cumulative
FROM monthly
ORDER BY month;

/* -------------------------------------------------------------------------- */
/* QUERY 5: gnars-vote-participation                                          */
/* -------------------------------------------------------------------------- */
WITH vote_logs AS (
        SELECT
                'base' AS chain,
                block_time,
                tx_hash,
                contract_address,
                topic0,
                topic2,
                data
        FROM base.logs
        WHERE contract_address = 0x3dd4e53a232b7b715c9ae455f4e732465ed71b4c
            AND topic0 IN (
                0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4,
                0xe2babfbac5889a709b63bb7f598b324e08bc5a4fb9ec647fb3cbc9ec07eb8712
            )

        UNION ALL

        SELECT
                'ethereum' AS chain,
                block_time,
                tx_hash,
                contract_address,
                topic0,
                topic2,
                data
        FROM ethereum.logs
        WHERE contract_address = 0x156e94a6e16244ccfdf16e1193198ea9d80dd7e3
            AND topic0 IN (
                0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4,
                0xe2babfbac5889a709b63bb7f598b324e08bc5a4fb9ec647fb3cbc9ec07eb8712
            )
)
SELECT
        chain,
        BYTEARRAY_TO_UINT256(topic2) AS proposal_id,
        block_time,
        BYTEARRAY_TO_UINT256(SUBSTR(data, 1, 32)) AS support,
        BYTEARRAY_TO_UINT256(SUBSTR(data, 33, 32)) AS votes_cast,
        tx_hash,
        contract_address,
        CASE
                WHEN topic0 = 0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4 THEN 'VoteCast'
                WHEN topic0 = 0xe2babfbac5889a709b63bb7f598b324e08bc5a4fb9ec647fb3cbc9ec07eb8712 THEN 'VoteCastWithParams'
                ELSE 'UnknownVoteEvent'
        END AS vote_event
FROM vote_logs
ORDER BY block_time DESC;
