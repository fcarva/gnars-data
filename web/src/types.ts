export type NavKey =
  | "home"
  | "community"
  | "projects"
  | "governance"
  | "timeline"
  | "network"
  | "treasury"
  | "archive";

export type Meta = {
  title: string;
  description: string;
  pathname: string;
  activeNav: NavKey;
};

export type AssetAmount = {
  symbol: string;
  amount: number;
};

export type ReferenceLink = {
  label: string;
  url: string;
  kind: string;
};

export type LinkItem = {
  label: string;
  href: string;
};

export type SearchEntry = {
  title: string;
  href: string;
  kind: string;
  summary: string;
};

export type PersonRecord = {
  person_id: string;
  slug: string;
  display_name: string;
  address: string;
  address_short: string;
  status: string;
  role: string;
  roles: string[];
  tags: string[];
  domains: string[];
  bio: string;
  identity: {
    member_url?: string | null;
    farcaster?: string | null;
    github?: string | null;
    avatar_url?: string | null;
    website?: string | null;
    x?: string | null;
    instagram?: string | null;
  };
  governance: {
    holder_token_count: number;
    delegated_token_count: number;
    active_votes: number;
    votes_count: number;
    attendance_pct: number | null;
    like_pct: number | null;
    proposals_authored_count: number;
    votes_cast_count: number;
  };
  receipts: {
    eth_received: number;
    usdc_received: number;
    gnars_received: number;
    fungible_transfer_count: number;
    nft_received_count: number;
    nft_transfer_count: number;
    by_asset: AssetAmount[];
    nft_assets: { label: string; count: number }[];
  };
  relationships: {
    authored_proposals: string[];
    voted_proposals: string[];
    payout_proposals: string[];
    owned_projects: string[];
    related_projects: string[];
    related_updates: string[];
  };
  notes: string;
};

export type SpendLedgerRecord = {
  ledger_id: string;
  archive_id: string;
  proposal_key: string;
  proposal_number: number | null;
  title: string;
  status: string;
  chain: string;
  project_id: string | null;
  project_name: string | null;
  proposer: string;
  proposal_end_at: string | null;
  proposal_created_at: string | null;
  asset_symbol: string;
  asset_name: string;
  asset_kind: string;
  token_contract: string | null;
  recipient_address: string;
  recipient_display_name: string;
  amount: number;
  source_url: string;
  canonical_url: string;
};

export type ProjectRollupRecord = {
  project_id: string;
  slug: string;
  name: string;
  status: string;
  category: string;
  origin_proposals: string[];
  proposal_summaries: {
    proposal_key: string;
    archive_id: string;
    proposal_number: number | null;
    title: string;
    status: string;
  }[];
  owner_addresses: string[];
  budget: {
    eth: number;
    usdc: number;
    gnars: number;
  };
  spent: {
    eth: number;
    usdc: number;
    gnars: number;
  };
  utilization_pct: {
    eth: number | null;
    usdc: number | null;
    gnars: number | null;
  };
  recipients: {
    address: string;
    display_name: string;
    eth_received: number;
    usdc_received: number;
    gnars_received: number;
    fungible_transfer_count: number;
    nft_received_count: number;
  }[];
  nft_receipts: {
    address: string;
    display_name: string;
    contract_label: string;
    token_contract: string;
    count: number;
  }[];
  updates_count: number;
  update_ids: string[];
  last_update_date: string | null;
  objective: string;
  outputs: string[];
  kpis: string[];
  notes: string;
};

export type ProposalArchiveRecord = {
  archive_id: string;
  platform: string;
  space: string;
  chain: string;
  proposal_key: string;
  proposal_number: number | null;
  title: string;
  status: string;
  status_display: string;
  proposer: string;
  proposer_label: string | null;
  created_at: string;
  start_at: string;
  end_at: string;
  snapshot_block: number;
  quorum: number;
  choices: string[];
  scores_by_choice: number[];
  scores_total: number;
  content_markdown: string;
  content_summary: string;
  cover_image_url: string | null;
  transactions: Record<string, unknown>[];
  votes: Record<string, unknown>[];
  links: {
    source_url: string;
    canonical_url: string;
    discussion_url: string | null;
    explorer_url: string | null;
  };
  properties: Record<string, unknown>;
};

export type TimelineEventRecord = {
  event_id: string;
  date: string;
  title: string;
  summary: string;
  kind: string;
  status: string;
  project_id: string | null;
  project_name: string | null;
  archive_id: string | null;
  proposal_number: number | null;
  people_addresses: string[];
  proposal_ids: string[];
  links: string[];
  source: string;
  thumbnail_url: string | null;
};

export type NotesIndexRecord = {
  slug: string;
  title: string;
  section: string;
  href: string;
  excerpt: string;
};

export type DaoMetrics = {
  overview: {
    proposal_count: number;
    active_proposal_count: number;
    people_count: number;
    holders_count: number;
    delegates_count: number;
    contributors_count: number;
    athletes_count: number;
    recipients_count: number;
    proposers_count: number;
    workstream_count: number;
    treasury_assets_count: number;
    treasury_total_value_usd: number;
    outflows_eth: number;
    outflows_usdc: number;
    outflows_gnars: number;
    fungible_transfer_count: number;
    nft_transfer_count: number;
    proposal_status_counts: Record<string, number>;
  };
  treasury: {
    wallet_address: string;
    wallet_label: string;
    homepage_treasury_label_usd: number;
    treasury_page_total_value_usd: number;
    treasury_page_display_total_usd: number;
    assets: {
      symbol: string;
      name: string;
      amount: number;
      value_usd: number;
    }[];
  };
  leaderboards: Record<
    string,
    {
      display_name: string;
      address: string;
      slug: string;
      value: number;
      label: string;
    }[]
  >;
  recent: {
    proposals: {
      archive_id: string;
      proposal_number: number | null;
      title: string;
      status: string;
      end_at: string;
    }[];
    payouts: {
      ledger_id: string;
      archive_id: string;
      asset_symbol: string;
      amount: number;
      recipient_display_name: string;
      recipient_address: string;
      project_id: string | null;
      proposal_end_at: string | null;
    }[];
    workstreams: {
      project_id: string;
      name: string;
      status: string;
      last_update_date: string | null;
    }[];
  };
};

export type ActivityTimeseriesRecord = {
  date: string;
  proposals_created: number;
  proposals_closed: number;
  proposals_executed: number;
  proposals_defeated: number;
  proposals_cancelled: number;
  proposals_active: number;
  payouts_count: number;
  payouts_eth: number;
  payouts_usdc: number;
  payouts_gnars: number;
  updates_count: number;
  deliveries_count: number;
};

export type ActivityTimeseriesData = {
  dataset: "activity_timeseries";
  as_of: string;
  version: number;
  granularity: string;
  records: ActivityTimeseriesRecord[];
};

export type TreasuryFlowRoute = {
  route_id: string;
  event_at: string;
  archive_id: string;
  proposal_key: string;
  proposal_number: number | null;
  proposal_title: string;
  proposal_status: string;
  proposal_chain: string;
  project_id: string | null;
  project_name: string | null;
  proposer_address: string;
  recipient_address: string;
  recipient_display_name: string;
  asset_symbol: string;
  amount: number;
  asset_kind: string;
  token_contract: string | null;
  proposal_href: string;
};

export type TreasuryFlowsData = {
  dataset: "treasury_flows";
  as_of: string;
  version: number;
  routes: TreasuryFlowRoute[];
  windows: {
    window_id: string;
    label: string;
    since: string | null;
    route_count: number;
    proposal_count: number;
    recipient_count: number;
    project_count: number;
    totals_by_asset: AssetAmount[];
    top_recipients: {
      address: string;
      display_name: string;
      totals: AssetAmount[];
    }[];
    top_projects: {
      project_id: string;
      project_name: string;
      totals: AssetAmount[];
    }[];
  }[];
  proposal_routes: {
    archive_id: string;
    proposal_number: number | null;
    proposal_title: string;
    proposal_status: string;
    proposal_chain: string;
    project_id: string | null;
    project_name: string | null;
    totals_by_asset: AssetAmount[];
    route_count: number;
    recipients: {
      address: string;
      display_name: string;
      totals_by_asset: AssetAmount[];
    }[];
  }[];
};

export type CommunitySignalsData = {
  dataset: "community_signals";
  as_of: string;
  version: number;
  windows: {
    window_id: string;
    label: string;
    since: string | null;
    metrics: {
      active_proposals_now: number;
      proposal_count: number;
      successful_proposal_count: number;
      payout_count: number;
      delivery_count: number;
      recipient_count: number;
      payouts_by_asset: AssetAmount[];
    };
    top_recipients: {
      address: string;
      display_name: string;
      totals_by_asset: AssetAmount[];
    }[];
    top_projects: {
      project_id: string;
      project_name: string;
      status: string;
      totals_by_asset: AssetAmount[];
    }[];
    top_proposals: {
      archive_id: string;
      proposal_number: number | null;
      title: string;
      status: string;
      totals_by_asset: AssetAmount[];
    }[];
    top_people: {
      address: string;
      display_name: string;
      received_totals: AssetAmount[];
      authored_count: number;
      delivery_count: number;
      score: number;
      tribes: string[];
    }[];
  }[];
  field_notes: {
    note_id: string;
    window_id: string;
    kind: string;
    title: string;
    summary: string;
  }[];
};

export type GraphNode = {
  node_id: string;
  kind: string;
  label: string;
  href: string;
  status?: string;
  tags?: string[];
  address?: string;
  size?: number;
  proposal_number?: number | null;
  metrics: Record<string, unknown>;
};

export type GraphEdge = {
  edge_id: string;
  source: string;
  target: string;
  kind: string;
  weight: number;
  count: number;
  asset_symbol?: string | null;
  href?: string | null;
};

export type NetworkGraphData = {
  dataset: "network_graph";
  as_of: string;
  version: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  views: {
    homepage: {
      node_ids: string[];
      edge_ids: string[];
    };
  };
};

export type NetworkViewNode = GraphNode & {
  x: number;
  y: number;
  radius: number;
};

export type NetworkViewEdge = GraphEdge & {
  sourceNode: NetworkViewNode;
  targetNode: NetworkViewNode;
};

export type NetworkViewData = {
  dataset: "network_view";
  as_of: string;
  version: number;
  width: number;
  height: number;
  nodes: NetworkViewNode[];
  edges: NetworkViewEdge[];
  homepage: {
    node_ids: string[];
    edge_ids: string[];
  };
  filters: {
    tribes: string[];
    assets: string[];
    statuses: string[];
  };
};

export type TreasuryViewScene = {
  window_id: string;
  label: string;
  width: number;
  height: number;
  route_count: number;
  total_value: number;
  nodes: {
    id: string;
    label: string;
    kind: string;
    x0: number;
    x1: number;
    y0: number;
    y1: number;
    value: number;
  }[];
  links: {
    link_id: string;
    source: string;
    target: string;
    value: number;
    width: number;
    asset_symbol: string;
    href?: string | null;
    path: string;
  }[];
};

export type TreasuryViewData = {
  dataset: "treasury_view";
  as_of: string;
  version: number;
  scenes: TreasuryViewScene[];
};

export type ActivityViewScene = {
  window_id: string;
  label: string;
  width: number;
  height: number;
  max_value: number;
  points: {
    index: number;
    date: string;
    governance: number;
    treasury: number;
    deliveries: number;
  }[];
  paths: {
    governance: string | null;
    treasury: string | null;
    deliveries: string | null;
  };
};

export type ActivityViewData = {
  dataset: "activity_view";
  as_of: string;
  version: number;
  scenes: ActivityViewScene[];
};

export type CommunityCard = {
  slug: string;
  href: string;
  displayName: string;
  subtitle: string;
  tribes: string[];
  totalReceivedLabel: string;
  approvedProposals: number;
  budgetManagedLabel: string;
  featured: boolean;
};

export type ProjectCard = {
  id: string;
  href: string;
  title: string;
  status: string;
  category: string;
  summary: string;
  proposalTag: string;
  budgetLabel: string;
  updatedAt: string;
};

export type ProposalCard = {
  archiveId: string;
  href: string;
  numberLabel: string;
  title: string;
  status: string;
  proposerLabel: string;
  budgetLabel: string;
  summary: string;
  projectLabel: string | null;
};

export type TimelineCard = {
  eventId: string;
  kind: string;
  status: string;
  dateLabel: string;
  title: string;
  summary: string;
  href: string | null;
  people: LinkItem[];
  project: LinkItem | null;
};

export type HomePageProps = {
  asOf: string;
  metrics: {
    label: string;
    value: string;
    detail: string;
  }[];
  hero: {
    title: string;
    description: string;
  };
  economicMap: NetworkViewData;
  activity: ActivityViewScene;
  treasuryScene: TreasuryViewScene;
  signalWindow: CommunitySignalsData["windows"][number];
  fieldNotes: CommunitySignalsData["field_notes"];
  featuredCommunity: CommunityCard[];
  featuredProjects: ProjectCard[];
  governance: ProposalCard[];
  timeline: TimelineCard[];
  leaderboards: {
    title: string;
    items: {
      label: string;
      value: string;
      href: string;
    }[];
  }[];
};

export type CommunityIndexPageProps = {
  filters: string[];
  people: CommunityCard[];
  economicMap: NetworkViewData;
};

export type CommunityProfilePageProps = {
  profile: {
    displayName: string;
    address: string;
    addressShort: string;
    tribes: string[];
    role: string;
    bio: string;
    links: ReferenceLink[];
    avatarUrl: string | null;
  };
  economics: {
    totalReceivedPrimary: AssetAmount | null;
    totalReceivedByAsset: AssetAmount[];
    approvedProposals: number;
    budgetManagedByAsset: AssetAmount[];
  };
  governanceMetrics: {
    activeVotes: number;
    votesCast: number;
    attendancePct: number | null;
    likePct: number | null;
    proposalSuccessRate: number;
    deliveryCount: number;
  };
  governanceLog: {
    href: string;
    numberLabel: string;
    title: string;
    status: string;
    budgetLabel: string;
    endedAt: string;
  }[];
  participation: {
    href: string;
    numberLabel: string;
    title: string;
    status: string;
  }[];
  projects: LinkItem[];
  proofOfWork: TimelineCard[];
  activity: ActivityViewScene;
  networkNeighbors: {
    label: string;
    href: string;
    kind: string;
    relationship: string;
    valueLabel: string;
  }[];
};

export type ProjectsPageProps = {
  filters: string[];
  projects: ProjectCard[];
  featuredLineage: TreasuryViewScene;
};

export type ProjectDetailPageProps = {
  project: ProjectCard & {
    objective: string;
    outputs: string[];
    kpis: string[];
    budgetByAsset: AssetAmount[];
    spentByAsset: AssetAmount[];
    utilization: {
      label: string;
      value: string;
    }[];
    recipients: {
      label: string;
      href: string;
      amounts: AssetAmount[];
    }[];
    proposalLinks: LinkItem[];
    timeline: TimelineCard[];
    recipientDistribution: AssetAmount[];
    treasuryScene: TreasuryViewScene | null;
  };
};

export type ProposalsPageProps = {
  proposals: ProposalCard[];
  signals: CommunitySignalsData["windows"][number];
};

export type ProposalDetailPageProps = {
  proposal: ProposalCard & {
    createdAt: string;
    endAt: string;
    choices: string[];
    scoresByChoice: number[];
    contentSummary: string;
    proposalLinks: ReferenceLink[];
    recipients: {
      label: string;
      href: string | null;
      amounts: AssetAmount[];
    }[];
    relatedPeople: LinkItem[];
    relatedProject: LinkItem | null;
    flowLineage: AssetAmount[];
    treasuryScene: TreasuryViewScene | null;
  };
};

export type TimelinePageProps = {
  timeline: TimelineCard[];
  activity: ActivityViewScene;
};

export type NetworkPageProps = {
  scene: NetworkViewData;
  highlights: {
    title: string;
    items: {
      label: string;
      detail: string;
      href: string;
    }[];
  }[];
};

export type TreasuryPageProps = {
  treasuryScene: TreasuryViewScene;
  windows: TreasuryFlowsData["windows"];
  proposalRoutes: TreasuryFlowsData["proposal_routes"];
};

export type NotesPageProps = {
  notes: NotesIndexRecord[];
};

export type PagePayload =
  | {
      pageType: "home";
      meta: Meta;
      props: HomePageProps;
    }
  | {
      pageType: "community-index";
      meta: Meta;
      props: CommunityIndexPageProps;
    }
  | {
      pageType: "community-profile";
      meta: Meta;
      props: CommunityProfilePageProps;
    }
  | {
      pageType: "projects-index";
      meta: Meta;
      props: ProjectsPageProps;
    }
  | {
      pageType: "project-detail";
      meta: Meta;
      props: ProjectDetailPageProps;
    }
  | {
      pageType: "proposals-index";
      meta: Meta;
      props: ProposalsPageProps;
    }
  | {
      pageType: "proposal-detail";
      meta: Meta;
      props: ProposalDetailPageProps;
    }
  | {
      pageType: "timeline-index";
      meta: Meta;
      props: TimelinePageProps;
    }
  | {
      pageType: "network-index";
      meta: Meta;
      props: NetworkPageProps;
    }
  | {
      pageType: "treasury-index";
      meta: Meta;
      props: TreasuryPageProps;
    }
  | {
      pageType: "notes-index";
      meta: Meta;
      props: NotesPageProps;
    };
