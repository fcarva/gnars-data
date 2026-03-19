# Gnars DAO Analytics Brief

Data basis: canonical repo artifacts in `data/`, with mixed timestamps across build outputs. Core metrics come from `data/dao_metrics.json` (`as_of` 2026-03-19), while `data/community_signals.json` and `data/treasury_flows.json` are newer build artifacts (`as_of` 2026-03-21). `data/project_rollups.json` remains anchored at 2026-03-18.

## Executive Summary

Gnars is operating as a large social graph with a narrow active core. The repo currently tracks 1,172 merged identities, but only 436 unique voters, 68 proposers, 49 recipients, and 35 athletes. That means the community surface is broad, while governance and capital routing are still concentrated in a small group of addresses and recurring workstream owners.

The treasury is small but liquid, with about $45.7k in assets and 25.82 ETH plus 194.2k USDC routed out through governance. Recent activity is real, but conversion into successful outcomes is weak: lifetime proposal success is 47.37%, and the last 30 days show 4 proposals with 0 successful closes.

The strongest product signal is not “downloads” or raw exports. It is the economic map itself: who proposes, who receives, which workstreams are fully funded, and where the same few operators keep reappearing across governance, treasury, and delivery.

## Treasury Flows

- Treasury composition is dominated by USDC at roughly 46.8% of reported value. SENDIT is the only meaningful secondary asset at about 10.4%; WETH is tiny, and the remaining tokens are effectively symbolic.
- The treasury balance is reported at $45,702.28 in `dao_metrics.json`, but the same file still shows `treasury_page_display_total_usd` as `0.0` and the homepage label as `$46.5k`. That is a visible data/UI mismatch that should be fixed.
- Outflows are concentrated: 81 fungible transfers and 37 NFT transfers are recorded, but 64 proposals account for all routed fungible value.
- Recipient concentration is high. The top 10 recipients absorb 63.17% of USDC outflows and 89.15% of ETH outflows.
- The most important routed proposal is `gnars-base-118`, which moved 1.5 ETH and 3,000 USDC to the Q1 2026 operations workstream. Proposal `gnars-base-111` moved 0.25 ETH and 900 USDC into the earlier docs/governance revamp.
- In the last 30 days, the treasury routed 9 payout transactions across 5 active recipients, totaling 2.4 ETH and 5,900 USDC.

## Proposal History

- The archive contains 193 proposals in total.
- Outcome mix: 65 executed, 101 closed, 12 defeated, 12 cancelled, and 3 currently active.
- Lifetime success rate is 47.37% across 190 closed outcomes.
- The most transaction-heavy proposals are `gnars-base-118` (18 tx), `gnars-base-119` (13 tx), `gnars-base-32` (8 tx), `gnars-base-96` (7 tx), and `gnars-base-30` (5 tx).
- The most vote-heavy proposals are older event/community proposals, with 45-46 votes on several items. That suggests historical attention is strongest around live events and cultural programming, not just infrastructure.
- Current active proposals are `119 Pod Media Strategy - Q1 2026`, `118 Gnars Operations - Q1 2026 Workstream Proposal`, and `35 Mexico can be Gnar.lier`.
- Recent governance momentum is present but not converting into closes: the 30-day window shows 4 proposals, 27 unique voters, 11.75 average votes per proposal, and 0 successful proposals.

## People And Community Signals

- The merged identity base is large: 1,172 people.
- The active governance layer is much smaller: 992 delegates, 1,011 holders, 91 contributors, 49 recipients, 68 proposers, and only 436 unique voters observed.
- The most visible operators are concentrated in a few nodes. `r4topunk`, `vlad`, and `fcarva` anchor the current operations workstream and appear repeatedly in receipts, updates, and proposal routing.
- Top ETH receivers are led by `0x387a...fffd` at 10.36 ETH, followed by `0x33bb...63ea` at 3.39 ETH and `0xe8b2...599d` at 3.0 ETH.
- Top USDC receivers are led by `0xe5f6...8beb` at 24,915 USDC, followed by `0xe1b9...9641` at 16,116 USDC and `0xbb4e...ef62` at 15,964 USDC.
- The recent 30-day top people window confirms that the active people graph is also the treasury graph: the same addresses show up as recipients, builders, proposers, and delivery participants.

## Projects And Workstreams

- There are only 2 tracked workstreams in the repo, which makes the project layer easy to read but too thin for a mature DAO.
- `Gnars Operations - Q1 2026 Workstream` is the only active workstream. It is fully utilized on paper: 1.5 ETH and 3,000 USDC budgeted, 1.5 ETH and 3,000 USDC spent, 100% utilization on both assets, 3 updates, and 5 outputs.
- `Gnars Revamp: Docs and Governance` is superseded, but also fully spent: 0.25 ETH and 900 USDC.
- Both workstreams currently tell you how much was spent, but not whether the delivery changed behavior, improved retention, or produced measurable community value. That is the current analytical gap.
- The operations workstream is the right nucleus for the new atlas because it already connects proposal lineage, treasury routing, owners, recipient splits, and public updates.

## Concentration Risks

- Treasury concentration is high in two dimensions: asset mix and recipient mix.
- Asset concentration: the top 2 assets hold 57.21% of reported treasury value.
- Recipient concentration: the top 10 recipients capture 63.17% of USDC and 89.15% of ETH outflows.
- Operational concentration: one active workstream accounts for all recent project spend, so the DAO is not yet diversified across multiple delivered programs.
- Governance concentration: 68 proposers and 436 unique voters across 1,172 identities means the decision surface is active, but the effective steering group is still relatively small.

## Missing Derived Metrics

- `proposal_tags.json` is not yet useful for taxonomy analysis: the current pilot set is still effectively `uncategorized`, so category-level spend and success analysis is blocked.
- Burn rate and runway are not yet computed from treasury history, which would be the single most useful budget-health metric.
- Proposal aging and latency are missing: time from creation to close/execution should be a first-class KPI.
- Category success rates are missing: proposals should be grouped by category, chain, and workstream to show where governance actually works.
- Delivery value per dollar is missing: workstreams need a `spent vs shipped` metric, not just utilization.
- Recipient concentration over time is missing: the current concentration view is static, not a trend.
- Voter retention and delegate activity by month are missing, so participation quality cannot be measured yet.
- Proof coverage is missing: the repo should count how many proposals, recipients, and workstreams have external proof links, media references, or verifiable updates.

## Bottom Line

Gnars already has enough data to behave like a real DAO analytics product, not a data dump. The strongest next move is to formalize taxonomies, add runway and success-by-category metrics, and turn the current economic map into an exploratory dashboard with filters and trend views.
