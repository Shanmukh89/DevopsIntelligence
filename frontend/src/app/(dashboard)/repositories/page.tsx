import React from "react";
import Link from "next/link";
import { GitBranch, RefreshCw, ExternalLink } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { RepositoryCard } from "@/components/dashboard/repository-card";

export const dynamic = "force-dynamic";

export default async function RepositoriesPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  // Fetch the user's auth provider
  const { data: profile } = await supabase
    .from("profiles")
    .select("auth_provider")
    .eq("id", user?.id)
    .single();

  const isGithubUser = profile?.auth_provider === 'github';

  // Fetch the user's GitHub App installation
  const { data: installation } = await supabase
    .from("github_installations")
    .select("github_account_login, repository_selection, github_installation_id")
    .eq("profile_id", user?.id)
    .single();

  // Fetch all repos linked to the installation (all are active)
  const { data: repositories } = await supabase
    .from("repositories")
    .select("*")
    .eq("profile_id", user?.id)
    .eq("is_active", true)
    .order("updated_at", { ascending: false });

  const appSlug = process.env.NEXT_PUBLIC_GITHUB_APP_SLUG || "auditr-dev";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1
            style={{
              fontSize: "var(--text-2xl)",
              fontWeight: 500,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Connected Repositories
          </h1>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
            {installation
              ? `Repositories from ${installation.github_account_login} (${installation.repository_selection === "all" ? "all repos" : "selected repos"})`
              : "Install the GitHub App to connect repositories."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {installation && (
            <a
              href={`https://github.com/settings/installations/${installation.github_installation_id}`}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 rounded-md transition-colors cursor-pointer hover:bg-white/5 border border-white/10"
              style={{
                padding: "8px 16px",
                color: "var(--text-secondary)",
                fontSize: "var(--text-sm)",
                fontWeight: 500,
              }}
            >
              <ExternalLink size={14} /> Manage on GitHub
            </a>
          )}
          {!installation && (
            <a
              href={`https://github.com/apps/${appSlug}/installations/new`}
              className="flex items-center gap-2 rounded-md transition-colors cursor-pointer"
              style={{
                padding: "8px 16px",
                backgroundColor: "var(--accent-500)",
                color: "#fff",
                fontSize: "var(--text-sm)",
                fontWeight: 500,
              }}
            >
              <RefreshCw size={14} /> {isGithubUser ? 'Import GitHub' : 'Connect GitHub'}
            </a>
          )}
        </div>
      </div>

      {!repositories || repositories.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-16 border border-white/5 rounded-xl bg-white/[0.02]">
          <GitBranch size={48} className="text-gray-600 mb-4" />
          <h3 className="text-gray-300 font-medium mb-1">No repositories connected</h3>
          <p className="text-sm text-gray-500 max-w-sm text-center mb-6">
            {installation
              ? "Your GitHub App installation has no repositories. Manage your installation on GitHub to add repositories."
              : isGithubUser
                ? "Install the Auditr GitHub App to import your repositories and pull requests."
                : "Install the Auditr GitHub App to import your repositories."}
          </p>
          <a
            href={installation
              ? `https://github.com/settings/installations/${installation.github_installation_id}`
              : `https://github.com/apps/${appSlug}/installations/new`
            }
            target={installation ? "_blank" : "_self"}
            rel="noreferrer"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 transition-colors text-white text-sm font-medium rounded-lg"
          >
            {installation ? "Manage on GitHub" : isGithubUser ? "Import GitHub" : "Connect GitHub"}
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {repositories.map((repo) => (
            <RepositoryCard key={repo.id} repo={repo} />
          ))}
        </div>
      )}
    </div>
  );
}
