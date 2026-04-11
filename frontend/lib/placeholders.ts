import type {
  ActivityItem,
  BuildRecord,
  DashboardStats,
  PRReview,
  Repository,
  Vulnerability,
} from "@/types";

export const placeholderRepositories: Repository[] = [
  {
    id: "demo-1",
    name: "auditr-core",
    fullName: "acme/auditr-core",
    defaultBranch: "main",
    url: "https://github.com/acme/auditr-core",
    connectedAt: new Date().toISOString(),
  },
  {
    id: "demo-2",
    name: "platform-api",
    fullName: "acme/platform-api",
    defaultBranch: "main",
    url: "https://github.com/acme/platform-api",
    connectedAt: new Date().toISOString(),
  },
];

export const placeholderDashboardStats: DashboardStats = {
  totalRepositories: 2,
  prsReviewedThisWeek: 14,
  buildSuccessRate: 0.94,
  vulnerabilitiesFound: 3,
};

export const placeholderActivity: ActivityItem[] = [
  {
    id: "a1",
    type: "build",
    title: "Build succeeded",
    description: "main @ auditr-core",
    timestamp: new Date(Date.now() - 3600_000).toISOString(),
  },
  {
    id: "a2",
    type: "pr",
    title: "PR reviewed",
    description: "#142 — Add rollout checks",
    timestamp: new Date(Date.now() - 7200_000).toISOString(),
  },
  {
    id: "a3",
    type: "alert",
    title: "Security alert",
    description: "Medium severity in dependency",
    timestamp: new Date(Date.now() - 86400_000).toISOString(),
  },
];

export function placeholderPRReviews(repoId: string): PRReview[] {
  return [
    {
      id: "pr-1",
      repositoryId: repoId,
      prNumber: 142,
      title: "Add rollout checks",
      state: "open",
      reviewedAt: new Date().toISOString(),
      summary: "LGTM with minor nits on error handling.",
    },
  ];
}

export function placeholderBuilds(repoId: string): BuildRecord[] {
  return [
    {
      id: "b1",
      repositoryId: repoId,
      status: "success",
      branch: "main",
      commitSha: "a1b2c3d",
      startedAt: new Date(Date.now() - 600_000).toISOString(),
      finishedAt: new Date(Date.now() - 598_000).toISOString(),
      durationSeconds: 120,
    },
  ];
}

export function placeholderVulnerabilities(repoId: string): Vulnerability[] {
  return [
    {
      id: "v1",
      repositoryId: repoId,
      severity: "medium",
      title: "Example CVE placeholder",
      packageName: "example-lib",
      detectedAt: new Date().toISOString(),
    },
  ];
}
