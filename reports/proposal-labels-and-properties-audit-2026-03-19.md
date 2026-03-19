# Proposal Labels And Properties Audit

Date: 2026-03-19

Scope:
- `data/proposals_archive.json`
- `data/proposals_enriched.json`
- `data/feed_stream.json`
- `data/filter_facets.json`
- agent feedback from `Peirce`, `Sartre`, and `Tesla`

## Executive read

The proposal layer already has enough information to drive the product, but it is split across three levels:

1. Raw archive fields from `proposals_archive.json`
2. Product-facing normalized fields in `proposals_enriched.json`
3. Overly source-shaped labels in `feed_stream.json`

The main issue is not lack of data. The issue is that the current labels mix:
- editorial meaning
- source/platform metadata
- domain artifacts
- transport details

The fix is to keep raw proposal properties for audit, but expose grouped, product-grade labels for UI and analytics.

## What proposals already contain

### Canonical raw proposal properties

Every archive record currently includes:

- `archive_id`
- `proposal_key`
- `proposal_number`
- `title`
- `status`
- `status_display`
- `platform`
- `chain`
- `proposer`
- `proposer_label`
- `created_at`
- `start_at`
- `end_at`
- `quorum`
- `scores_total`
- `scores_by_choice`
- `choices`
- `snapshot_block`
- `space`
- `content_markdown`
- `content_summary`
- `cover_image_url`
- `links`
- `properties`
- `transactions`
- `votes`
- `raw_snapshot`

Important:
- `archive_id` is the only stable global identifier.
- `proposal_number` is useful for display, not for joins.
- `properties` is raw source payload and should not be used as a public UI contract.

### Platform-specific raw properties

`gnars.com` proposal `properties` commonly include:

- `proposalId`
- `proposalNumber`
- `title`
- `description`
- `proposer`
- `status`
- `proposerEnsName`
- `createdAt`
- `endBlock`
- `snapshotBlock`
- `endDate`
- `forVotes`
- `againstVotes`
- `abstainVotes`
- `quorumVotes`
- `calldatas`
- `targets`
- `values`
- `signatures`
- `transactionHash`

`snapshot` proposal `properties` commonly include:

- `id`
- `title`
- `body`
- `choices`
- `start`
- `end`
- `state`
- `author`
- `type`
- `scores`
- `scores_total`
- `scores_by_strategy`
- `created`
- `network`
- `symbol`
- `quorum`
- `discussion`
- `plugins`
- `privacy`
- `snapshot`

Conclusion:
- `properties` is useful for debugging and audit.
- It is not stable enough to power labels or public fields directly.

## What the product layer already derives

`data/proposals_enriched.json` already gives a strong base:

- `archive_id`
- `proposal_key`
- `proposal_number`
- `title`
- `status`
- `platform`
- `chain`
- `proposer`
- `proposer_label`
- `created_at`
- `start_at`
- `end_at`
- `date`
- `successful`
- `hot`
- `closing_soon`
- `category`
- `scope_labels`
- `project_ids`
- `recipient_addresses`
- `recipient_count`
- `requested_by_asset`
- `routed_by_asset`
- `vote_count`
- `scores_total`
- `quorum`
- `quorum_met`
- `proof_count`
- `related_proof_ids`
- `reference_urls`
- `summary`
- `href`

Current category distribution:

- `Media`: 90
- `Governance`: 48
- `Operations`: 14
- `Athlete Support`: 11
- `Events`: 11
- `Travel`: 8
- `Software`: 8
- `Other`: 3

Current status distribution:

- `closed`: 101
- `executed`: 65
- `cancelled`: 12
- `defeated`: 12
- `active`: 3

Current top `scope_labels`:

- `single-recipient`: 189
- `snapshot`: 104
- `closed`: 101
- `gnars.com`: 92
- `Media`: 90
- `base`: 80
- `executed`: 65
- `Governance`: 48
- `Operations`: 14
- `cancelled`: 12
- `defeated`: 12
- `Athlete Support`: 11
- `Events`: 11
- `ethereum`: 9
- `Travel`: 8
- `Software`: 8
- `multi-recipient`: 4
- `active`: 3
- `Other`: 3
- `linked-project`: 2

Conclusion:
- `scope_labels` is useful, but too mixed.
- It combines category, status, platform, chain, and structure in one flat array.

## What the feed layer currently gets wrong

`data/feed_stream.json` works for rendering a mixed stream, but many labels are source-shaped instead of product-shaped.

Top feed labels currently include:

- `reference`
- `web`
- `image`
- `social`
- `i.imgur.com`
- `hackmd.io`
- `www.instagram.com`
- `executed`
- `ipfs.skatehive.app`
- `snapshot`
- `closed`
- `gnars.com`
- `Media`
- `contributor`
- `community`
- `treasury`

Conclusion:
- domains like `hackmd.io`, `i.imgur.com`, and `paragraph.com` should not be public proposal labels
- they should become secondary metadata:
  - `source_domain`
  - `reference_kind`
  - `reference_channel`

## Recommended label groups

Replace proposal-facing flat labels with grouped labels.

### 1. `editorial_labels`

Public-facing topical meaning:

- `operations`
- `media`
- `events`
- `travel`
- `athlete-support`
- `software`
- `governance`
- `treasury`
- `other`

### 2. `status_labels`

Public-facing lifecycle state:

- `active`
- `executed`
- `defeated`
- `cancelled`
- `closed`
- `pending`

### 3. `funding_labels`

What kind of capital behavior the proposal expresses:

- `funding-request`
- `treasury-policy`
- `no-direct-spend`
- `eth`
- `usdc`
- `gnars`
- `multi-asset`
- `single-asset`
- `nft`

### 4. `relationship_labels`

How the proposal connects to the rest of the DAO graph:

- `linked-project`
- `single-recipient`
- `multi-recipient`
- `athlete-linked`
- `builder-linked`
- `operations-linked`
- `media-proof`
- `project-proof`

### 5. `platform_labels`

Secondary provenance only:

- `base`
- `ethereum`
- `snapshot`
- `gnars.com`

### 6. `lifecycle_labels`

Needed for feed grouping and project lineage:

- `proposal`
- `funded`
- `in-delivery`
- `delivered`
- `proof-added`
- `archival`

### 7. `proof_labels`

Only when a real artifact exists:

- `video`
- `article`
- `thread`
- `report`
- `drop`
- `photo`
- `doc`

## Recommended proposal properties by product surface

### Proposal cards

Use:

- `archive_id`
- `proposal_number`
- `title`
- `status`
- `category`
- `editorial_labels`
- `summary_short`
- `proposer_display`
- `date`
- `requested_total_display`
- `requested_by_asset`
- `routed_by_asset`
- `recipient_count`
- `project_ids`
- `proof_count`
- `hot`
- `closing_soon`
- `href`

Best visible order:

1. `Prop #`
2. `STATUS`
3. `CATEGORY`
4. `Title`
5. `Summary`
6. `Requested budget`
7. `Proposer`
8. `Project / recipients / proof`

### Governance ledger rows

Use:

- `proposal_number`
- `title`
- `status`
- `category`
- `proposer_display`
- `project_label`
- `requested_total_display`
- `routed_total_display`
- `vote_count`
- `end_at`
- `platform`
- `chain`

Optional detail-only fields:

- `quorum`
- `scores_total`
- `scores_by_choice`
- `transaction_count`

### Proposal detail hero

Use:

- `proposal_number`
- `title`
- `status`
- `category`
- `proposer_display`
- `requested_total_display`
- `routed_by_asset`
- `recipient_count`
- `linked project`
- `proof_count`
- `created_at`
- `start_at`
- `end_at`

### Proposal detail metadata rail

Use:

- `platform`
- `chain`
- `vote_count`
- `scores_total`
- `quorum`
- `quorum_met`
- `successful`
- `reference_channels`

### Profile backlinks

Every profile should be able to show proposal links with:

- `archive_id`
- `proposal_number`
- `title`
- `status`
- `category`
- `person_role_in_proposal`
- `requested_by_asset`
- `routed_to_person_by_asset`
- `project_ids`
- `proof_count`
- `date`
- `href`

Recommended `person_role_in_proposal` values:

- `author`
- `recipient`
- `project-owner`
- `voter`
- `mentioned`
- `proof-subject`

### Project lineage

Every project should consume proposal rows with:

- `archive_id`
- `proposal_number`
- `title`
- `status`
- `category`
- `proposal_role_in_project`
- `requested_by_asset`
- `routed_by_asset`
- `recipient_addresses`
- `proof_count`
- `reference_urls`

Recommended `proposal_role_in_project` values:

- `origin`
- `budget-extension`
- `ops-support`
- `delivery-update`
- `treasury-route`
- `media-proof`

### Homepage feed items

Use:

- `item_id`
- `kind`
- `date`
- `status`
- `title`
- `summary`
- `editorial_labels`
- `status_labels`
- `linked_people`
- `linked_projects`
- `linked_proposals`
- `linked_assets`
- `primary_href`

Recommended visible feed labels:

- `PROP ACTIVE`
- `PROP PASSED`
- `PROP DEFEATED`
- `PAYOUT`
- `PROJECT UPDATE`
- `DELIVERY`
- `MEDIA PROOF`

## New derived proposal properties worth adding

These are the most useful missing derivations.

### High priority

- `summary_short`
- `requested_total_display`
- `routed_total_display`
- `editorial_labels`
- `status_labels`
- `funding_labels`
- `relationship_labels`
- `platform_labels`
- `lifecycle_labels`
- `reference_channels`
- `primary_recipients`
- `proposal_type`
- `delivery_stage`
- `proof_strength`
- `lineage_strength`

### Useful relational fields

- `person_role_in_proposal`
- `proposal_role_in_project`
- `proposal_subjects`

### Useful sizing/filter fields

- `budget_shape`
- `is_terminal`
- `is_active`
- `outcome_group`
- `winning_choice`

Recommended values:

`proposal_type`
- `funding`
- `ops`
- `governance-change`
- `ratification`
- `delivery-update`
- `treasury-policy`
- `signal-only`

`delivery_stage`
- `pre-funding`
- `funded`
- `in-progress`
- `proof-linked`
- `delivered`

`proof_strength`
- `none`
- `reference-only`
- `delivery-proof`
- `multi-proof`

`lineage_strength`
- `direct-origin`
- `direct-budget`
- `supporting`
- `proof-only`
- `adjacent`

`budget_shape`
- `no-budget`
- `micro`
- `mid`
- `large`
- `multi-recipient`

## What should stay raw-only

Keep these for audit/debug, not primary public chips:

- `properties`
- `raw_snapshot`
- raw contract addresses
- raw token addresses
- raw source domains
- raw transaction payload internals
- raw model metadata from `proposal_tags`

Also:
- `proposal_tags.json` is not ready to drive public labels yet
- it is still mostly queued and null-filled

## Important cautions

- `proposal_number` is display-only, not globally unique
- `archive_id` must remain the global join key
- `transactions` must not be equated with realized spend by default
- `choices` and `scores_by_choice` need normalization before success analytics
- NFT transfers must stay separate from fungible budget/spend everywhere
- `proposer_label` is too sparse to be relied on directly

## Recommended implementation order

1. Split `scope_labels` into grouped label arrays
2. Add `summary_short` and display totals
3. Normalize feed labels away from domains and raw reference types
4. Add role fields:
   - `person_role_in_proposal`
   - `proposal_role_in_project`
5. Add proposal lifecycle and proof fields:
   - `delivery_stage`
   - `proof_strength`
   - `lineage_strength`
6. Keep raw proposal properties intact for audit only

## Bottom line

The proposal layer already has the information the project needs.

The right move is not to add more raw labels. The right move is to reorganize them into:

- topical labels
- status labels
- funding labels
- relationship labels
- lifecycle labels
- proof labels

That gives the site a proposal system that fits:

- dense `noun.wtf`-style lists
- `nouns.camp`-style structure
- people, treasury, project, and proof multiplicity
