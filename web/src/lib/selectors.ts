import type {
  AssetAmount,
  PersonRecord,
  ProjectRollupRecord,
  ProposalArchiveRecord,
  SpendLedgerRecord,
  TimelineEventRecord,
} from "../types";
import { formatAmount, shortAddress, titleCase } from "./format";

export function communityHref(slug: string): string {
  return `/community/${slug}/`;
}

export function projectHref(projectId: string): string {
  return `/projects/${projectId}/`;
}

export function proposalHref(archiveId: string): string {
  return `/proposals/${archiveId}/`;
}

export function timelineHrefIndex(): string {
  return "/timeline/";
}

export function treasuryHref(): string {
  return "/treasury/";
}

export function networkHref(): string {
  return "/network/";
}

export function notesHref(): string {
  return "/notes/";
}

export function tribeLabels(tags: string[]): string[] {
  const ordered = ["athlete", "filmmaker", "builder", "organizer", "delegate", "holder", "proposer", "recipient", "contributor"];
  const seen = new Set<string>();
  const labels: string[] = [];
  for (const tag of [...ordered, ...tags]) {
    if (!tags.includes(tag) || seen.has(tag)) {
      continue;
    }
    seen.add(tag);
    labels.push(titleCase(tag));
  }
  return labels.length ? labels : ["Community"];
}

export function isSuccessfulProposal(record: ProposalArchiveRecord): boolean {
  if (record.platform === "gnars.com" || record.platform === "gnars") {
    return record.status === "executed";
  }
  if (record.platform === "snapshot" && record.status === "closed") {
    if (record.scores_total < record.quorum) {
      return false;
    }
    const firstChoice = Number(record.scores_by_choice[0] ?? 0);
    const maxChoice = Math.max(...record.scores_by_choice.map((value) => Number(value)));
    return firstChoice > 0 && firstChoice === maxChoice;
  }
  return false;
}

export function groupAssetTotals(records: { asset_symbol: string; amount: number }[]): AssetAmount[] {
  const totals = new Map<string, number>();
  for (const record of records) {
    totals.set(record.asset_symbol, (totals.get(record.asset_symbol) ?? 0) + record.amount);
  }
  return [...totals.entries()]
    .map(([symbol, amount]) => ({
      symbol,
      amount: Number(amount.toFixed(8)),
    }))
    .sort((left, right) => right.amount - left.amount);
}

export function proposalBudgetLabel(records: SpendLedgerRecord[]): string {
  const totals = groupAssetTotals(records);
  if (!totals.length) {
    return "No treasury routing";
  }
  return totals.map((item) => formatAmount(item.symbol, item.amount)).join(" + ");
}

export function getAthleteEconomics(
  walletAddress: string,
  spendLedger: SpendLedgerRecord[],
  proposals: ProposalArchiveRecord[],
  ownedProjectIds: string[],
): {
  totalReceivedPrimary: AssetAmount | null;
  totalReceivedByAsset: AssetAmount[];
  approvedProposals: number;
  budgetManagedByAsset: AssetAmount[];
} {
  const wallet = walletAddress.toLowerCase();
  const successfulProposalIds = new Set(
    proposals.filter((proposal) => isSuccessfulProposal(proposal)).map((proposal) => proposal.archive_id),
  );
  const successfulAuthoredIds = proposals
    .filter((proposal) => proposal.proposer.toLowerCase() === wallet && isSuccessfulProposal(proposal))
    .map((proposal) => proposal.archive_id);
  const managedLedgerIds = new Set<string>();
  const managedRecords: SpendLedgerRecord[] = [];
  const relevantProposalIds = new Set<string>(successfulAuthoredIds);

  for (const record of spendLedger) {
    if (record.project_id && ownedProjectIds.includes(record.project_id) && successfulProposalIds.has(record.archive_id)) {
      relevantProposalIds.add(record.archive_id);
    }
  }

  for (const record of spendLedger) {
    if (!successfulProposalIds.has(record.archive_id)) {
      continue;
    }
    if (relevantProposalIds.has(record.archive_id) && !managedLedgerIds.has(record.ledger_id)) {
      managedLedgerIds.add(record.ledger_id);
      managedRecords.push(record);
    }
  }

  const received = spendLedger.filter(
    (record) => record.recipient_address.toLowerCase() === wallet && successfulProposalIds.has(record.archive_id),
  );
  const totalReceivedByAsset = groupAssetTotals(received);
  const budgetManagedByAsset = groupAssetTotals(managedRecords);

  return {
    totalReceivedPrimary: totalReceivedByAsset[0] ?? null,
    totalReceivedByAsset,
    approvedProposals: successfulAuthoredIds.length,
    budgetManagedByAsset,
  };
}

export function personLabel(record: PersonRecord): string {
  return record.display_name || record.identity.ens || record.identity.farcaster || shortAddress(record.address);
}

export function personIdentityLabel(record: PersonRecord): string {
  return record.identity.ens || shortAddress(record.address);
}

export function personSubtitle(record: PersonRecord): string {
  if (record.bio) {
    return record.bio;
  }
  return record.role || "Gnars community member";
}

export function timelineHref(record: TimelineEventRecord): string | null {
  if (record.archive_id) {
    return proposalHref(record.archive_id);
  }
  if (record.project_id) {
    return projectHref(record.project_id);
  }
  return record.links[0] ?? null;
}

export function projectBudgetAssets(record: ProjectRollupRecord): AssetAmount[] {
  return [
    { symbol: "ETH", amount: record.budget.eth },
    { symbol: "USDC", amount: record.budget.usdc },
    { symbol: "GNARS", amount: record.budget.gnars },
  ].filter((item) => item.amount > 0);
}

export function projectSpentAssets(record: ProjectRollupRecord): AssetAmount[] {
  return [
    { symbol: "ETH", amount: record.spent.eth },
    { symbol: "USDC", amount: record.spent.usdc },
    { symbol: "GNARS", amount: record.spent.gnars },
  ].filter((item) => item.amount > 0);
}
