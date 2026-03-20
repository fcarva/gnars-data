# Gnars Camp Site Surface and Proposal Context Audit

Date: 2026-03-20

## Public route inventory

Current static route model from [prerender.tsx](c:/Users/DELL/Documents/gnars-data/web/scripts/prerender.tsx):

- `/`
- `/community/`
- `/community/<slug>/`
- `/projects/`
- `/projects/<project_id>/`
- `/proposals/`
- `/proposals/<archive_id>/`
- `/timeline/`
- `/network/`
- `/treasury/`
- `/notes/`

Current prerender counts from the public data payloads:

- `1` home route
- `1` community index
- `1171` community profile routes
- `1` projects index
- `2` project detail routes
- `1` proposals index
- `193` proposal detail routes
- `1` timeline route
- `1` network route
- `1` treasury route
- `1` notes route
- `1374` total prerendered routes

## gnars.com proposal vocabulary and context fields

Observed on the live `gnars.com` surfaces on 2026-03-20:

### Homepage / dashboard language

Homepage and dashboard language is activity-first, not dataset-first.

Examples from [gnars.com](https://www.gnars.com/):

- `Live Feed`
- `Voting Closing Soon`
- `Vote on Proposal #118`
- `voted FOR with 134 votes`
- `Bid`
- `Auction`

Meaning:

- proposal context on `gnars.com` is expressed through actions and public verbs
- the product vocabulary is closer to `activity + governance + treasury movement` than to analytics terminology
- if Gnars Camp wants to stay legible to the same audience, proposal labels should keep this action language visible

### Proposal index vocabulary

Observed on [gnars.com/proposals](https://www.gnars.com/proposals):

- `Prop #119`
- `Active`
- `Base`
- `by 0x2feb...5aed6a`
- `6 days ago`
- `Voting Progress 925 votes`
- `Requested 0.5 ETH + 2,900 USDC`
- `Requested No direct ETH/USDC transfer`

Stable proposal list fields from the source UI:

- proposal number
- status
- chain
- title
- proposer short address
- relative recency
- voting progress / vote total
- requested budget summary

This is important because the current Gnars Camp proposal list does not yet preserve all of this structure in one row.

### Proposal detail vocabulary

Observed on [Proposal #118](https://www.gnars.com/proposals/base/118):

- explicit `Budget` section
- contributor-role table
- `Why Vote Yes`
- `Proposed Transactions`
- repeated `Transfer to`
- treasury source (`from DAO Treasury`)
- fungible values (`0.6 ETH`, `1,200 USDC`)
- NFT receipts (`5 Gnars NFTs`, token ids)

Stable proposal detail fields from the source UI:

- contributor / role / budget table
- argument / rationale section
- proposed transfer breakdown
- treasury source
- recipient short address
- fungible asset routing
- NFT routing

Meaning:

- proposal meaning on `gnars.com` is not only governance metadata
- it is also `requested budget + human roles + concrete routing plan`
- Gnars Camp should expose that same structure when it exists

### About page vocabulary

Observed on [gnars.com/about](https://www.gnars.com/about):

- `community owned skate brand`
- `Members propose ideas, vote, and fund projects`
- `video parts, events, public installations`
- `Auctions help fund the treasury`

Meaning:

- the category model should stay culturally grounded
- category labels should not drift into generic DAO jargon
- the bridge is: auctions -> treasury -> proposals -> people -> projects

## Page-by-page audit

## `/`

Current implementation:

- mixed live feed
- signal rail
- map
- concentration and category summaries

What is thin or misleading:

- the home page says `economic map first`, but the `gnars.com` source language is more `live feed first`
- `Concentration` currently shows treasury concentration but does not always explain the asset basis clearly enough
- `Field Notes` are useful but often detached from explicit source provenance
- the home page map claims filterability indirectly, but no direct map controls are exposed there

Most important fixes:

- keep action-language labels in the feed: `Vote`, `Funded`, `Delivery`, `Proof`, `Auction`
- show explicit `as of` and asset basis on every financial summary
- attach feed items back to proposal / person / project lineages more aggressively

Data dependencies:

- `feed_stream.json`
- `community_signals.json`
- `network_view.json`
- `activity_view.json`
- `insights.json`
- `filter_facets.json`

## `/community/`

Current implementation:

- directory + network map
- filters for tribe and status

What is thin or misleading:

- the page says people are more than wallets, but rows still do not show enough governance or treasury lineage context
- the map consumes too much explanatory space versus the directory rows
- there is no explicit distinction between curated identities, ENS-resolved identities, and address-only identities
- tribe/status filters are not enough for the actual use cases; proposer / recipient / delegate / holder views matter

Most important fixes:

- add role-based filters beyond `tribe`
- show `ENS / address / identity confidence` directly in rows
- add proposal counts, receipt totals, and proof counts as first-class row fields
- demote the map slightly and promote the table/list rhythm

Data dependencies:

- `people.json`
- `network_graph.json`
- `community_signals.json`
- stronger identity provenance fields in the people dataset

## `/community/<slug>/`

Current implementation:

- strong dossier structure
- scoreboard
- governance log
- proof of work
- neighbors
- references

What is thin or misleading:

- `References` currently mixes identity links, project links, and participation links into one bucket
- the page does not always explain what counts as `Total Received` versus broader project-associated value
- there is no transaction-grade treasury ledger per person
- authored proposals and participation are visible, but proposal roles are still under-modeled

Most important fixes:

- separate `Identity`, `Governance`, `Treasury`, `Projects`, `Proof`
- add recipient-level treasury route ledger
- add explicit `successful / defeated / active` authored proposal split
- expose identity provenance: curated label, ENS verified, address-only

Data dependencies:

- `people.json`
- `spend_ledger.json`
- `proposals_enriched.json`
- `project_rollups.json`
- `timeline_events.json`

## `/projects/`

Current implementation:

- dense registry list with category and status filters

What is thin or misleading:

- only `2` project detail routes currently exist, which means project coverage is much narrower than proposal coverage
- many proposal-backed efforts are not represented as project records
- `proposalTag` is singular and too thin for multi-proposal lineage
- owner / contributor / proof coverage are not visible at index level

Most important fixes:

- make it explicit that project coverage is incomplete relative to proposals
- add multi-proposal lineage labels
- show owners / contributors / proof count / routed spend
- consider pseudo-project or workstream rollups for proposal clusters that never became canonical projects

Data dependencies:

- `project_rollups.json`
- `projects.json`
- `project_updates.json`
- proposal-to-project derivation logic

## `/projects/<project_id>/`

Current implementation:

- funding split
- outputs
- recipients
- proposal lineage
- proof of work

What is thin or misleading:

- requested budget vs realized routed budget is still not explicit enough
- there is no proof-quality or proof-source breakdown
- recipients are shown, but operational roles are not
- treasury lineage is there, but not yet dense enough for audit reading

Most important fixes:

- explicitly separate `approved`, `routed`, and `spent`
- attach proof sources and dates at row level
- show owner / contributor / recipient roles separately
- give proposal lineage more than one text row per proposal

Data dependencies:

- `project_rollups.json`
- `media_proof.json`
- `project_updates.json`
- `spend_ledger.json`

## `/proposals/`

Current implementation:

- dense ledger
- filters for status/category/window
- search and sort

What is thin or misleading:

- it is still missing some of the strongest `gnars.com` list semantics:
  - chain
  - proposer short address / ENS secondary
  - voting progress framing
  - explicit `requested` language
- current row model compresses requested and routed too aggressively
- `No direct ETH/USDC transfer` is a meaningful source phrase and should remain visible as such
- proposal meaning is still underspecified when it is governance-only, policy-only, or NFT-heavy

Most important fixes:

- preserve `requested` vs `routed` in the row itself
- show chain/platform
- show proposer primary + secondary identity
- keep `no direct ETH/USDC transfer` language when applicable
- show proposal type labels such as `funding`, `treasury policy`, `signal-only`, `delivery update`

Data dependencies:

- `proposals_enriched.json`
- `proposals_archive.json`
- `feed_stream.json`
- proposal-type derivation
- requested / routed / NFT split

## `/proposals/<archive_id>/`

Current implementation:

- proposal file
- flow lineage
- recipients
- related people
- choice set

What is thin or misleading:

- this is the biggest proposal-context gap in the site
- current proposal detail does not yet mirror the full meaning visible on `gnars.com`
- missing or underexposed:
  - chain/platform prominence
  - proposer secondary identity
  - requested budget table
  - explicit rationale / purpose section
  - proposed transactions ledger
  - NFT routing
  - vote interpretation
  - source-specific fields and proposal properties

Most important fixes:

- add a `proposal header` with status, chain, proposer, requested, routed, proof strength
- add `requested vs routed vs NFT transfers`
- add `proposed transactions` table with recipient, asset, amount, token contract, transaction kind
- add a richer `governance outcome` section: scores, quorum, winning choice
- add source context blocks parsed from markdown / raw properties when stable enough

Data dependencies:

- `proposals_archive.json`
- `proposals_enriched.json`
- `spend_ledger.json`
- `media_proof.json`
- stable parsing from `content_markdown`

## `/timeline/`

Current implementation:

- chronology + activity chart

What is thin or misleading:

- timeline is useful, but the event labels are still too generic for a page that should function as public memory
- there are no filters
- source provenance is not visible enough
- proposal / treasury / proof events need stronger separation at row level

Most important fixes:

- add filters by event kind and status
- show source labels and linked proposal/project chips
- expose proof / treasury / governance verbs more clearly

Data dependencies:

- `timeline_events.json`
- `feed_stream.json`
- event provenance fields

## `/network/`

Current implementation:

- full map + highlight lists

What is thin or misleading:

- the page copy says the graph is filterable by tribe, asset, and status, but the current UI does not actually expose those controls
- highlight lists are useful, but the graph itself can overstate legibility without an inspector or row fallback

Most important fixes:

- add real network filters or remove the claim
- add node inspector / adjacency table
- expose edge kinds more clearly

Data dependencies:

- `network_graph.json`
- `network_view.json`
- filter facets for the graph surface

## `/treasury/`

Current implementation in the current local branch:

- moving toward a treasury ledger + grouped Sankey model
- route tables, recipients, categories, proposal lineage

What is still thin or misleading:

- long-tail / opaque asset labels still degrade trust
- current holdings, all-time routed value, and recent inactivity need stronger separation
- Sankey still risks carrying too much of the page meaning
- proposal lineage needs explicit requested vs routed vs zero-route separation
- identity trust cues need to be consistent in dense rows

Most important fixes:

- keep the Sankey secondary to the route ledger
- normalize or explicitly bucket long-tail token labels
- add chain filter
- add last routed date / inactivity / quality note
- add concentration panels by core asset
- add asset provenance cues: native ETH, ERC-20, unverified token

Data dependencies:

- `treasury_flows.json`
- `insights.json`
- `treasury_snapshots.json`
- `people.json`
- better unknown-token normalization in derivation

## `/notes/`

Current implementation:

- archive index only
- note cards with section/title/excerpt

What is thin or misleading:

- the archive currently behaves as a searchable note board, not a true Quartz-like knowledge surface
- note detail is not modeled as its own route type in the current prerender system
- archive cards are disconnected from the people / project / proposal graph

Most important fixes:

- make archive intent explicit: index-only or detail-capable
- if index-only, link notes into entity detail pages more aggressively
- if Quartz-like detail remains the goal, add note detail routes and backlinks

Data dependencies:

- `notes_index.json`
- search index
- note-to-entity backlink derivation

## Highest-priority product/data bugs

1. Proposal detail is the thinnest high-value page.

Why it matters:

- this is where source context, routing plan, and governance meaning should converge
- right now it is still thinner than `gnars.com`

2. Project coverage is under-complete.

Why it matters:

- the site promises `proposal -> project -> delivery`, but only `2` project detail routes currently exist

3. Treasury meaning still needs stronger truth-constraints.

Why it matters:

- current holdings, routed capital, and inactivity must not be conflated
- unknown tokens must not pollute the main financial read

4. Community identity confidence is underexposed.

Why it matters:

- ENS/display names help, but the UI needs to show when an identity is curated, ENS-verified, or only address-derived

5. Proposal list rows still underuse source semantics.

Why it matters:

- `gnars.com` gives a clear proposal row grammar
- Gnars Camp should keep that structure while adding deeper analytics, not replace it with abstraction

## Stable proposal fields that should drive labeling

These are strong enough for product use:

- proposal number
- status
- chain
- platform
- proposer address
- proposer label / ENS when verified
- created / start / end
- requested totals
- routed totals
- recipient count
- proof count
- transaction kinds
- linked project ids
- proposal type
- delivery stage
- proof strength
- lineage strength

## Fields that should stay source-shaped or low-confidence

- raw `properties` blobs
- noisy domain strings used directly as product labels
- long-tail token symbols derived only from contract-like prefixes
- unparsed markdown sections without stable heading mapping
- pilot-only tagging metadata from `proposal_tags.json`

## Immediate next implementation moves

1. Finish the treasury page refactor with:
   - cleaner asset semantics
   - chain filter
   - concentration panels
   - quality / inactivity rail

2. Upgrade proposal detail to match the source grammar:
   - requested budget
   - proposed transactions
   - rationale / why vote
   - NFT transfers
   - source provenance

3. Harden the people/project surfaces around identity confidence and incomplete project coverage.
