# Proposal Tagging Guidelines

Use this guide to tag proposals consistently across `gnars.com` and `Snapshot`.

## Goal

Turn unstructured proposal text into a reviewable machine layer that supports:

- proposal search and clustering
- weekly governance digests
- success-rate analytics by category
- funding mix analysis
- builder directory enrichment

## Tagging workflow

1. Start with the proposal title, summary, body, decoded transactions, and linked discussion.
2. Assign exactly one `primary_category`.
3. Add zero or more `secondary_categories` only when they materially help search or reporting.
4. Set `funding_category` only when the proposal requests or moves assets.
5. Set `lifecycle_stage` based on what the proposal is trying to do, not just current vote status.
6. If model confidence is below `0.80`, keep `requires_human_review = true`.

## Primary categories

- `governance`: constitutional changes, voting process, delegation, meta-governance
- `operations`: DAO operations, reporting, coordination, admin, community maintenance
- `media`: editorial, content, social, video, storytelling, distribution
- `brand`: design systems, identity, marketing, campaigns, templates
- `product`: apps, dashboards, infrastructure, tooling, APIs, analytics
- `events`: contests, sessions, meetups, activations, tours, demos
- `grants`: direct support for builders, skaters, artists, filmmakers, partners
- `treasury`: asset management, swaps, custody, treasury policy, budget controls
- `onchain`: smart contracts, deployments, protocol integrations, token mechanics
- `archive`: historical resolutions, retrospectives, recordkeeping

## Secondary categories

Use these only when they add retrieval value:

- `athletes`
- `artists`
- `content`
- `contracts`
- `contests`
- `dao-ops`
- `data`
- `delegation`
- `documentation`
- `education`
- `funding`
- `governance-process`
- `grants-program`
- `identity`
- `irl`
- `media-distribution`
- `onboarding`
- `partner-ecosystem`
- `reporting`
- `skate-culture`
- `treasury-ops`

## Funding categories

- `none`: no budget request and no asset movement
- `eth`: native ETH transfer requested
- `usdc`: USDC transfer requested
- `nft`: NFT transfer requested
- `mixed`: multiple assets requested
- `treasury-policy`: treasury rule change without immediate spend

## Lifecycle stages

- `signal`: announcement, temperature check, resolution, sentiment
- `funding-request`: budget or grant request
- `delivery`: execution, continuation, or extension of funded work
- `infrastructure`: tooling, contracts, process, data systems
- `retrospective`: report-back, audit, recap, accountability

## Entity extraction

Capture canonical names only when clearly present:

- builders or teams
- partner orgs
- products and tools
- ecosystems and protocols

Examples:

- `Pod Media`
- `Gnarly News`
- `Snapshot`
- `NounsGG`
- `Zora`

## Confidence policy

- `>= 0.90`: safe to batch-approve after spot checks
- `0.80 - 0.89`: normal review lane
- `< 0.80`: mandatory human review

## Pilot scope

The initial pilot is `30` proposals. Use the pilot to validate:

- category coverage
- confidence thresholds
- tag usefulness for search and reporting
- consistency across `gnars.com` and legacy `Snapshot` proposals
