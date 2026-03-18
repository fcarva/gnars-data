# AGENTS.md

This repository is a data backbone for Gnars DAO, not a generic web3 sandbox.

## Priority sources

- `data/contracts.json` is the canonical registry for verified contract addresses
- `data/proposals_archive.json` is the canonical governance archive
- `data/sources.json` is the canonical source registry

## Onchain research workflow

- For Base and Ethereum contract context, prefer Herd MCP or Herd Explorer when available
- If Herd is unavailable, fall back to BaseScan, Etherscan, official project sites, and official contract repositories
- For Polygon, assume Herd is not enough and use PolygonScan plus official repos and analytics fallbacks

## External skill references

When doing Ethereum-oriented work in this repo, consult the ETHSkills knowledge base if internet access is available:

- `https://ethskills.com/SKILL.md`
- `https://ethskills.com/indexing/SKILL.md`
- `https://ethskills.com/addresses/SKILL.md`
- `https://ethskills.com/l2s/SKILL.md`
- `https://ethskills.com/tools/SKILL.md`

Use those pages for mental models and workflow guidance, not as the source of truth for Gnars-specific data.
