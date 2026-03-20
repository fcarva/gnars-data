# Site And Proposal Context Audit

Date: 2026-03-20

Scope:
- local public site surfaces in `web/src/pages/`
- current prerender route registry in `web/scripts/prerender.tsx`
- proposal datasets:
  - `data/proposals_archive.json`
  - `data/proposals_enriched.json`
  - `data/proposal_tags.json`
  - `data/project_rollups.json`
  - `data/people.json`
- public source surfaces on `gnars.com`

Primary source pages checked on 2026-03-20:
- `https://www.gnars.com/about`
- `https://www.gnars.com/proposals`
- `https://www.gnars.com/proposals/base/111`
- `https://www.gnars.com/proposals/base/118`
- `https://www.gnars.com/proposals/6`
- `https://www.gnars.com/treasury`

## Executive read

The repo already has enough raw information to make proposal labels and page context much stronger, but three things are still mixed together:

1. `source truth fields`
2. `derived product labels`
3. `editorial interpretation`

The right move is not to push more raw proposal payload into the UI. The right move is to make the proposal layer explicit:

- stable governance facts
- stable treasury facts
- stable relationship facts
- derived product labels
- manual curation only where meaning is genuinely ambiguous

The current local site already has the right page set. What it still lacks is tighter source-grounded context:

- what a proposal asked for
- what the DAO actually routed
- who authored it
- who received it
- what kind of proposal it was
- whether it produced proof
- whether it belongs to a larger delivery lineage

## Public site inventory

Current page types from `web/src/pages/` and `web/scripts/prerender.tsx`:

- `/`
  - `HomePage.tsx`
  - mixed feed / live surface
- `/community/`
  - `CommunityIndexPage.tsx`
  - people explorer
- `/community/<slug>/`
  - `CommunityProfilePage.tsx`
  - person dossier
- `/projects/`
  - `ProjectsPage.tsx`
  - project registry
- `/projects/<project_id>/`
  - `ProjectDetailPage.tsx`
  - project dossier
- `/proposals/`
  - `ProposalsPage.tsx`
  - governance ledger
- `/proposals/<archive_id>/`
  - `ProposalDetailPage.tsx`
  - proposal file
- `/treasury/`
  - `TreasuryPage.tsx`
  - treasury routing / concentration / lineage
- `/network/`
  - `NetworkPage.tsx`
  - graph surface
- `/timeline/`
  - `TimelinePage.tsx`
  - chronology
- `/notes/`
  - `NotesPage.tsx`
  - archive

Conclusion:
- the route inventory is already broad enough
- the next gains are semantic, not structural
- proposal labeling and source context are the main missing layer across almost every page

## What `gnars.com` clearly communicates

### 1. DAO framing

`/about` is consistent and stable enough to use as product language guidance:

- Gnars is a skateboarding collective
- it is community owned
- proposals are how support is allocated
- treasury and auctions are part of the system, but the cultural/community purpose is primary

This matters because labels should not drift into generic DAO jargon.

### 2. Proposal index semantics

`/proposals` exposes a stable proposal-card structure:

- proposal number
- status
- title
- proposer
- relative recency
- vote progress
- requested budget

This is the strongest public UI model for proposal list cards.

Fields clearly stable enough for product display:

- `proposal_number`
- `status`
- `title`
- `proposer`
- `requested amount`
- `chain / platform grouping`

### 3. Proposal detail semantics

`/proposals/base/111` and similar pages expose a stable detail structure:

- status
- title
- proposer
- for / against / abstain
- threshold
- ended date
- snapshot block
- description
- sometimes explicit budget sections
- proposed transactions

This is the strongest model for the `Proposal File` page in the local product.

Fields stable enough for proposal detail:

- `status`
- `proposer`
- `vote breakdown`
- `threshold / quorum-ish governance threshold`
- `ended at`
- `snapshot block`
- `description`
- `proposed transactions`

### 4. Treasury semantics

`/treasury` exposes a stable holdings-oriented treasury page:

- current holdings
- token holdings
- NFT holdings
- auction revenue
- proposal activity
- member activity

This confirms a useful separation:

- holdings and treasury position are one layer
- routed capital and proposal lineage are another layer

The local site should keep those layers distinct.

## Proposal fields: stable vs noisy vs derived

### Stable enough for product labeling

These can be treated as product-grade proposal facts:

- `archive_id`
- `proposal_key`
- `proposal_number`
- `title`
- `platform`
- `chain`
- `status`
- `proposer`
- `proposer_label`
- `created_at`
- `start_at`
- `end_at`
- `choices`
- `scores_total`
- `scores_by_choice`
- `quorum`
- `votes`
- `transactions`
- `links`
- `content_summary`
- `content_markdown`

These are stable enough because they recur across source surfaces and already behave like canonical identifiers or durable governance facts.

### Stable enough only as raw audit

These should stay in the repo but not drive public labels directly:

- `properties`
- platform-specific payload fields inside `properties`
- raw decoded transaction payload fragments
- raw source-specific transport details

Reason:
- too source-shaped
- too inconsistent across `gnars.com` and `snapshot`
- too easy to leak implementation details into product labels

### Should be derived

These should remain derived product fields:

- `successful`
- `hot`
- `closing_soon`
- `category`
- `summary_short`
- `requested_total_display`
- `routed_total_display`
- `proposal_type`
- `delivery_stage`
- `proof_strength`
- `lineage_strength`
- `reference_channels`
- `primary_recipients`
- `editorial_labels`
- `status_labels`
- `funding_labels`
- `relationship_labels`
- `platform_labels`
- `lifecycle_labels`
- `proof_labels`
- `project_ids`
- `recipient_addresses`
- `recipient_count`
- `proof_count`
- `related_proof_ids`

Reason:
- these are product interpretations, not source facts
- they should be deterministic and explainable
- they should be validated against the source layer, not copied from it

### Should be manually curated

These need editorial/manual override when high accuracy matters:

- ambiguous category assignments
- athlete vs builder vs organizer framing
- project lineage for proposals that do not explicitly map to `projects.json`
- proof significance
- “historic / foundational / policy / cultural” importance

Manual curation should be minimal and explicit. It should not be the default path for ordinary proposal labeling.

## Current dataset reality

From the current local data:

- proposals: `193`
- platforms:
  - `snapshot`: `101`
  - `gnars.com`: `92`
- categories:
  - `Media`: `88`
  - `Travel`: `24`
  - `Events`: `22`
  - `Athlete Support`: `20`
  - `Operations`: `14`
  - `Software`: `11`
  - `Governance`: `7`
  - `Other`: `7`
- proposal types:
  - `signal-only`: `92`
  - `funding`: `56`
  - `treasury-policy`: `18`
  - `delivery-update`: `17`
  - `ops`: `8`
  - `governance-change`: `2`
- delivery stages:
  - `proof-linked`: `134`
  - `pre-funding`: `38`
  - `funded`: `21`
- proposals with linked projects: `2`
- proposals with zero routed value: `150`

Interpretation:

- the repo is not short on proposal records
- it is short on explicit project lineage
- many proposals are governance/signal records, not direct treasury outflows
- this makes proposal typing and requested-vs-routed distinction essential

## Proposed taxonomy

### Category taxonomy

Keep the current closed product taxonomy:

- `Operations`
- `Media`
- `Events`
- `Travel`
- `Athlete Support`
- `Software`
- `Governance`
- `Other`

### Proposal type taxonomy

This is already close to right and should be kept:

- `funding`
- `signal-only`
- `treasury-policy`
- `delivery-update`
- `ops`
- `governance-change`
- `ratification`

Notes:
- `signal-only` should be explicitly read as “governance record without decoded direct treasury route”
- `delivery-update` should not imply fresh budget

### Delivery stage taxonomy

Keep this narrower and source-faithful:

- `pre-funding`
- `funded`
- `in-progress`
- `proof-linked`
- `delivered`

Current local data uses `proof-linked`, `pre-funding`, and `funded`; the remaining two should stay reserved for stronger project lineage.

### Relationship taxonomy

Keep these as explicit grouped labels, not a flat soup:

- `linked-project`
- `single-recipient`
- `multi-recipient`
- `athlete-linked`
- `builder-linked`
- `operations-linked`
- `media-proof`
- `project-proof`

### Funding taxonomy

Keep these separate from category:

- `funding-request`
- `no-direct-spend`
- `treasury-policy`
- asset labels:
  - `eth`
  - `usdc`
  - `gnars`
  - `sendit`
  - `token-*` for unverified long-tail ERC-20s
- `single-asset`
- `multi-asset`
- `nft`

## Concrete dataset corrections

### High priority

1. Stop treating `proposal_tags.json` as authoritative taxonomy.
- It should remain a seed / helper layer, not the public truth.

2. Keep `requested` and `routed` fully separate everywhere.
- Requested is a proposal ask.
- Routed is realized decoded treasury movement.
- Zero-route proposals must stay visible as governance records, but not be read as treasury outflow.

3. Treat `gnars.com` proposal detail structure as the reference shape for proposal detail pages.
- status
- proposer
- vote breakdown
- threshold
- ended
- snapshot block
- description
- proposed transactions

4. Make `proposal_number` display-only and `archive_id` join-only everywhere.
- This is already the safest rule and should be enforced consistently in selectors and route builders.

5. Stop implying project lineage where the repo does not actually have it.
- Current linked project coverage is too sparse to overstate.
- Use `proposal -> recipient` as the default treasury lineage.
- Only show `proposal -> project` when the mapping is explicit.

### Medium priority

6. Add stronger source-grounded context fields to proposal detail payloads.
- `vote_breakdown`
- `threshold_display`
- `snapshot_block_display`
- `description_sections_present`
- `has_proposed_transactions`

7. Separate `proof count` from `proof strength`.
- A proposal can have many references but weak proof.
- Count and strength should not be conflated.

8. Normalize proposal reference channels against actual source meaning.
- `website`
- `explorer`
- `farcaster`
- `youtube`
- `vimeo`
- `instagram`
- `paragraph`
- `mirror`
- `hackmd`
- `github`
- `zora`
- `image-host`

9. Mark low-confidence category assignments explicitly in the data pipeline.
- especially for proposals with weak text cues and no project mapping

### Low priority

10. Add editorial importance flags later.
- `historic`
- `policy`
- `foundational`
- `athlete-milestone`
- `delivery-milestone`

These are useful, but should come after the core proposal facts are cleaned.

## Page-level implications

### Home

Needs proposal context in feed rows, not just labels.

Every proposal feed row should be able to answer:

- what was asked
- what was routed
- whether it passed
- who it involved
- whether it has proof

### Community profile

Proposal participation should distinguish:

- authored
- voted
- paid through
- linked by delivery/proof

### Projects

Current project coverage is too sparse to carry all proposal context.

This page should not invent lineage. It should surface:

- explicit linked proposals
- explicit recipient routes
- explicit updates/proof

### Proposals

This is the page that should become most source-faithful to `gnars.com`.

Proposal rows need:

- number
- status
- title
- proposer
- requested
- routed
- category
- type
- proof count

### Treasury

Treasury should be the place where `requested vs routed` becomes visibly honest.

Proposal lineage table should emphasize:

- requested
- routed
- status
- recipients
- proof
- project only when explicit

## Resume point for implementation

Before resuming the interrupted treasury/page refactor, the next safe steps are:

1. Carry this proposal taxonomy into selectors/view-models instead of relying on mixed `labels`.
2. Use `gnars.com` proposal detail semantics to strengthen proposal detail and treasury lineage rows.
3. Keep zero-route proposals in governance surfaces, but never let them pollute routed treasury summaries.
4. Improve source-grounded cues across pages:
   - proposer
   - requested
   - routed
   - vote breakdown
   - proof strength
   - lineage confidence
5. Only after that, continue visual polishing and bug fixes page by page.
