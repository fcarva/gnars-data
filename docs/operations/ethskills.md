# ETHSkills

## Why it is relevant to `gnars-data`

ETHSkills is not a Gnars data source. It is a supplemental Ethereum knowledge base for agents and operators working on this repository.

It is useful when the task is about:

- indexing onchain data correctly
- choosing between Ethereum mainnet and L2 surfaces
- avoiding hallucinated contract addresses
- choosing current Ethereum tooling
- understanding current Ethereum development tradeoffs before changing scripts or schemas

## Recommended pages

- root skill: `https://ethskills.com/SKILL.md`
- indexing: `https://ethskills.com/indexing/SKILL.md`
- contract addresses: `https://ethskills.com/addresses/SKILL.md`
- L2s: `https://ethskills.com/l2s/SKILL.md`
- tools: `https://ethskills.com/tools/SKILL.md`

## How to use it in this repo

- use ETHSkills for workflow and architectural guidance
- use Herd for Base and Ethereum contract context when available
- use BaseScan, Etherscan, PolygonScan, official sites, and official repositories to confirm Gnars-specific facts
- keep final contract records in `data/contracts.json`
- keep final source registry updates in `data/sources.json`

## Boundary

ETHSkills improves agent judgment. It does not replace:

- contract explorer verification
- repository-level raw snapshots
- chain-specific source attribution
- Gnars-specific structured datasets
