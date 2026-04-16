/**
 * GitHub App — Sync Logic
 *
 * Installation-token-based repository and PR synchronization.
 * Replaces the old OAuth provider_token-based sync entirely.
 */

import { createClient } from '@/lib/supabase/server'
import { fetchInstallationRepos, fetchRepoPullRequests } from '@/lib/github/app'

// ---------------------------------------------------------------------------
// Repository Sync
// ---------------------------------------------------------------------------

/**
 * Fetches all repositories accessible to a GitHub App installation
 * and upserts them into Supabase. The installation's selected repos
 * = the user's granted repos. No client-side picker needed.
 */
export async function syncInstallationRepos(
  githubInstallationId: number,
  dbInstallationId: string,
  profileId: string
) {
  const supabase = await createClient()

  console.log(`[SYNC] Fetching repos for installation ${githubInstallationId}`)
  const githubRepos = await fetchInstallationRepos(githubInstallationId)
  console.log(`[SYNC] Found ${githubRepos.length} repos from GitHub`)

  if (githubRepos.length === 0) return []

  const mappedRepos = githubRepos.map((repo: any) => ({
    profile_id: profileId,
    installation_id: dbInstallationId,
    github_repo_id: repo.id,
    owner_login: repo.owner?.login || repo.full_name?.split('/')[0] || '',
    name: repo.name,
    full_name: repo.full_name,
    url: repo.html_url,
    provider: 'github',
    default_branch: repo.default_branch || 'main',
    language: repo.language || null,
    is_private: repo.private || false,
    is_active: true, // All installation repos are active
    last_synced_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }))

  const { data: upsertedRepos, error } = await supabase
    .from('repositories')
    .upsert(mappedRepos, { onConflict: 'github_repo_id' })
    .select('*')

  if (error) {
    console.error('[SYNC] Failed to upsert repos:', error)
    throw new Error(`Failed to sync repositories: ${error.message}`)
  }

  // Remove repos that are no longer in the installation
  // (user may have removed repos from the GitHub App)
  const currentGhIds = githubRepos.map((r: any) => r.id)
  await supabase
    .from('repositories')
    .update({ is_active: false })
    .eq('installation_id', dbInstallationId)
    .not('github_repo_id', 'in', `(${currentGhIds.join(',')})`)

  console.log(`[SYNC] Upserted ${upsertedRepos?.length || 0} repos`)
  return upsertedRepos || []
}

// ---------------------------------------------------------------------------
// Pull Request Sync
// ---------------------------------------------------------------------------

/**
 * Fetches recent PRs for all active repositories in an installation
 * and upserts them into Supabase.
 */
export async function syncInstallationPRs(
  githubInstallationId: number,
  dbInstallationId: string
) {
  const supabase = await createClient()

  // Get all active repos for this installation
  const { data: repos } = await supabase
    .from('repositories')
    .select('id, full_name')
    .eq('installation_id', dbInstallationId)
    .eq('is_active', true)

  if (!repos || repos.length === 0) {
    console.log('[SYNC] No active repos to sync PRs for')
    return
  }

  let totalPRs = 0

  for (const repo of repos) {
    if (!repo.full_name) continue

    try {
      const githubPRs = await fetchRepoPullRequests(
        githubInstallationId,
        repo.full_name,
        'all',
        30
      )

      if (githubPRs.length === 0) continue

      const mappedPRs = githubPRs.map((pr: any) => ({
        repository_id: repo.id,
        github_pr_id: pr.id,
        pr_number: pr.number,
        title: pr.title,
        author: pr.user?.login || 'unknown',
        status: pr.state === 'closed' && pr.merged_at ? 'merged' : pr.state,
        created_at: pr.created_at,
        updated_at: pr.updated_at || new Date().toISOString(),
      }))

      const { error } = await supabase
        .from('pull_requests')
        .upsert(mappedPRs, { onConflict: 'github_pr_id' })

      if (error) {
        console.error(`[SYNC] Failed to upsert PRs for ${repo.full_name}:`, error)
      } else {
        totalPRs += mappedPRs.length
      }
    } catch (e) {
      console.error(`[SYNC] Error syncing PRs for ${repo.full_name}:`, e)
    }
  }

  console.log(`[SYNC] Synced ${totalPRs} PRs across ${repos.length} repos`)
}

// ---------------------------------------------------------------------------
// Single PR Upsert (for webhook events)
// ---------------------------------------------------------------------------

/**
 * Upserts a single pull request from a webhook payload.
 */
export async function upsertPullRequest(prPayload: any, repoFullName: string) {
  const supabase = await createClient()

  // Find the repository in our DB
  const { data: repo } = await supabase
    .from('repositories')
    .select('id')
    .eq('full_name', repoFullName)
    .single()

  if (!repo) {
    console.warn(`[SYNC] PR webhook for unknown repo: ${repoFullName}`)
    return
  }

  const mapped = {
    repository_id: repo.id,
    github_pr_id: prPayload.id,
    pr_number: prPayload.number,
    title: prPayload.title,
    author: prPayload.user?.login || 'unknown',
    status: prPayload.state === 'closed' && prPayload.merged_at ? 'merged' : prPayload.state,
    created_at: prPayload.created_at,
    updated_at: prPayload.updated_at || new Date().toISOString(),
  }

  const { error } = await supabase
    .from('pull_requests')
    .upsert(mapped, { onConflict: 'github_pr_id' })

  if (error) {
    console.error('[SYNC] Failed to upsert PR from webhook:', error)
  }
}
