import type { CommunityCard, FeedStreamItem, ProjectCard, ProposalCard } from "../types";

function isAll(value: string) {
  return !value || value === "all";
}

function normalizeValue(value: string | null | undefined) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function inWindow(date: string | null | undefined, windowId: string) {
  if (isAll(windowId)) {
    return true;
  }
  if (!date) {
    return false;
  }
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) {
    return false;
  }
  const now = new Date();
  const days = windowId === "30d" ? 30 : windowId === "6m" ? 183 : 3650;
  return parsed.getTime() >= now.getTime() - days * 24 * 60 * 60 * 1000;
}

export function filterFeed(items: FeedStreamItem[], filters: { kind: string; status: string; window: string; search: string }) {
  const search = filters.search.trim().toLowerCase();
  return items.filter((item) => {
    if (!isAll(filters.kind) && item.kind !== filters.kind) {
      return false;
    }
    if (!isAll(filters.status) && item.status !== filters.status) {
      return false;
    }
    if (!inWindow(item.date, filters.window)) {
      return false;
    }
    if (search) {
      const haystack = `${item.title} ${item.summary} ${item.labels.join(" ")}`.toLowerCase();
      return haystack.includes(search);
    }
    return true;
  });
}

export function filterProposals(
  proposals: ProposalCard[],
  filters: { status: string; category: string; window: string; search: string; sort: string },
) {
  const search = filters.search.trim().toLowerCase();
  const filtered = proposals.filter((proposal) => {
    if (!isAll(filters.status) && proposal.statusKey !== filters.status) {
      return false;
    }
    if (!isAll(filters.category) && normalizeValue(proposal.category) !== filters.category) {
      return false;
    }
    if (!inWindow(proposal.date, filters.window)) {
      return false;
    }
    if (search && !proposal.searchText.toLowerCase().includes(search)) {
      return false;
    }
    return true;
  });

  return filtered.sort((left, right) => {
    switch (filters.sort) {
      case "budget_desc":
      case "routed_value_desc":
        return right.routedValue - left.routedValue || right.date.localeCompare(left.date);
      case "votes_desc":
        return right.voteCount - left.voteCount || right.date.localeCompare(left.date);
      case "date_desc":
      default:
        return right.date.localeCompare(left.date) || right.routedValue - left.routedValue;
    }
  });
}

export function filterCommunity(
  people: CommunityCard[],
  filters: { tribe: string; status: string; search: string; sort: string },
) {
  const search = filters.search.trim().toLowerCase();
  const filtered = people.filter((person) => {
    if (!isAll(filters.tribe) && !person.tribes.map((item) => item.toLowerCase()).includes(filters.tribe)) {
      return false;
    }
    if (!isAll(filters.status) && person.status !== filters.status) {
      return false;
    }
    if (search && !person.searchText.toLowerCase().includes(search)) {
      return false;
    }
    return true;
  });
  return filtered.sort((left, right) => {
    switch (filters.sort) {
      case "eth_received_desc":
        return right.ethReceived - left.ethReceived || right.displayName.localeCompare(left.displayName);
      case "usdc_received_desc":
        return right.usdcReceived - left.usdcReceived || right.displayName.localeCompare(left.displayName);
      case "budget_managed_desc":
        return right.budgetManagedPrimary - left.budgetManagedPrimary || right.displayName.localeCompare(left.displayName);
      case "proof_desc":
        return right.proofCount - left.proofCount || right.displayName.localeCompare(left.displayName);
      case "date_desc":
      default:
        return String(right.lastSeenAt ?? "").localeCompare(String(left.lastSeenAt ?? "")) || right.displayName.localeCompare(left.displayName);
    }
  });
}

export function filterProjects(
  projects: ProjectCard[],
  filters: { category: string; status: string; search: string; sort: string },
) {
  const search = filters.search.trim().toLowerCase();
  const filtered = projects.filter((project) => {
    if (!isAll(filters.category) && normalizeValue(project.categoryKey || project.category) !== filters.category) {
      return false;
    }
    if (!isAll(filters.status) && project.statusKey !== filters.status) {
      return false;
    }
    if (search && !project.searchText.toLowerCase().includes(search)) {
      return false;
    }
    return true;
  });
  return filtered.sort((left, right) => {
    switch (filters.sort) {
      case "proof_desc":
        return right.proofCount - left.proofCount || String(right.updatedAt).localeCompare(String(left.updatedAt));
      case "delivery_desc":
        return right.deliveryCount - left.deliveryCount || String(right.updatedAt).localeCompare(String(left.updatedAt));
      case "date_desc":
      default:
        return String(right.updatedAt).localeCompare(String(left.updatedAt)) || right.title.localeCompare(left.title);
    }
  });
}
