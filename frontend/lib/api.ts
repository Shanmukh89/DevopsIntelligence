import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import { getToken } from "@/lib/auth";
import type {
  ActivityItem,
  BuildRecord,
  CodebaseQuestionRequest,
  CodebaseQuestionResponse,
  DashboardStats,
  PRReview,
  Repository,
  Vulnerability,
} from "@/types";

const API_BASE =
  process.env["NEXT_PUBLIC_API_BASE_URL"] ?? "http://localhost/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function createClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: API_BASE.replace(/\/$/, ""),
    headers: {
      "Content-Type": "application/json",
    },
    timeout: 60_000,
    validateStatus: (status) => status >= 200 && status < 300,
  });

  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: unknown) => Promise.reject(normalizeAxiosError(error)),
  );

  instance.interceptors.response.use(
    (response) => response,
    (error: unknown) => Promise.reject(normalizeAxiosError(error)),
  );

  return instance;
}

function normalizeAxiosError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const ax = error as AxiosError<{ detail?: string; message?: string }>;
    const status = ax.response?.status;
    const data = ax.response?.data;
    const msg =
      (typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail?: unknown }).detail)
        : undefined) ??
      (typeof data === "object" && data !== null && "message" in data
        ? String((data as { message?: unknown }).message)
        : undefined) ??
      ax.message ??
      "Request failed";
    return new ApiError(msg, status, data);
  }
  if (error instanceof Error) {
    return new ApiError(error.message);
  }
  return new ApiError("Unknown error");
}

export const apiClient = createClient();

/** List connected repositories. */
export async function getRepositories(): Promise<Repository[]> {
  const { data } = await apiClient.get<Repository[]>("/repositories");
  return data;
}

/** Ask a question about the codebase (RAG / agent). */
export async function askCodebaseQuestion(
  payload: CodebaseQuestionRequest,
): Promise<CodebaseQuestionResponse> {
  const { data } = await apiClient.post<CodebaseQuestionResponse>(
    "/codebase/ask",
    payload,
  );
  return data;
}

/** PR reviews for a repository. */
export async function getPRReviews(
  repositoryId: string,
): Promise<PRReview[]> {
  const { data } = await apiClient.get<PRReview[]>(
    `/repositories/${encodeURIComponent(repositoryId)}/reviews`,
  );
  return data;
}

/** CI/CD build history. */
export async function getBuildHistory(
  repositoryId: string,
): Promise<BuildRecord[]> {
  const { data } = await apiClient.get<BuildRecord[]>(
    `/repositories/${encodeURIComponent(repositoryId)}/builds`,
  );
  return data;
}

/** Security vulnerabilities. */
export async function getVulnerabilities(
  repositoryId: string,
): Promise<Vulnerability[]> {
  const { data } = await apiClient.get<Vulnerability[]>(
    `/repositories/${encodeURIComponent(repositoryId)}/vulnerabilities`,
  );
  return data;
}

/** Aggregated dashboard stats (home). */
export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/dashboard/stats");
  return data;
}

/** Recent activity feed. */
export async function getRecentActivity(): Promise<ActivityItem[]> {
  const { data } = await apiClient.get<ActivityItem[]>("/dashboard/activity");
  return data;
}
