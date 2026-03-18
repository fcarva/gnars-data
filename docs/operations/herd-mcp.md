# Herd MCP

## Why it matters for `gnars-data`

Herd is a useful supplement when the repo needs richer onchain context than a flat explorer or CSV can provide.

Use it for:

- confirming proxy and implementation relationships
- decoding proposal execution transactions
- tracing wallet-to-contract relationships
- identifying what a deployer wallet created
- searching verified code for upgrade, admin, mint, auction, or treasury patterns

## Current coverage

Verified from Herd docs on `2026-03-18`:

- supported: `Ethereum`
- supported: `Base`
- not listed as supported: `Polygon`

That means Herd fits the current Gnars and That's Gnarly Base/Ethereum registry well, but it is not enough by itself for full multi-chain coverage.

## Position in this repo

- `data/contracts.json` remains the canonical contract registry
- `data/proposals_archive.json` remains the canonical governance archive
- Herd is a context and investigation layer, not the source of truth
- aggregate KPI work should still rely on Dune, exports, or dedicated sync scripts

## MCP endpoint

- endpoint: `https://mcp.herd.eco/v1`
- auth: client-side OAuth through the IDE MCP manager

Official docs:

- `https://docs.herd.eco/herd-mcp/introduction`
- `https://docs.herd.eco/herd-mcp/configuration`
- `https://docs.herd.eco/herd-app/explorer`
- `https://docs.herd.eco/herd-app/supported-chains`
