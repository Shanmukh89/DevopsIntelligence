export interface Repository {
  id: string;
  name: string;
  fullName: string;
  defaultBranch: string;
  url: string;
  connectedAt: string;
}

export interface CodebaseQuestionRequest {
  question: string;
  repositoryId: string;
}

export interface CodebaseQuestionResponse {
  answer: string;
  sources?: string[];
}

export interface PRReview {
  id: string;
  repositoryId: string;
  prNumber: number;
  title: string;
  state: "open" | "closed" | "merged";
  reviewedAt: string;
  summary?: string;
}

export interface BuildRecord {
  id: string;
  repositoryId: string;
  status: "success" | "failure" | "pending" | "running";
  branch: string;
  commitSha: string;
  startedAt: string;
  finishedAt?: string;
  durationSeconds?: number;
}

export interface Vulnerability {
  id: string;
  repositoryId: string;
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  packageName?: string;
  detectedAt: string;
}

export interface DashboardStats {
  totalRepositories: number;
  prsReviewedThisWeek: number;
  buildSuccessRate: number;
  vulnerabilitiesFound: number;
}

export interface ActivityItem {
  id: string;
  type: "build" | "pr" | "alert" | "repo";
  title: string;
  description: string;
  timestamp: string;
}
