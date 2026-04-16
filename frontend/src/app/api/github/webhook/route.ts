import { NextResponse } from 'next/server'
import { verifyWebhookSignature } from '@/lib/github/app'
import { syncInstallationRepos, syncInstallationPRs, upsertPullRequest } from '@/lib/github/sync'
import { createClient } from '@/lib/supabase/server'

/**
 * GitHub App Webhook Handler
 *
 * Receives events from GitHub and keeps our data in sync.
 * All payloads are verified via HMAC-SHA256 signature.
 */
export async function POST(request: Request) {
  const body = await request.text()
  const signature = request.headers.get('x-hub-signature-256') || ''
  const event = request.headers.get('x-github-event') || ''

  // 1. Verify webhook signature
  if (!verifyWebhookSignature(body, signature)) {
    console.error('[WEBHOOK] Invalid signature')
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
  }

  const payload = JSON.parse(body)
  const action = payload.action
  console.log(`[WEBHOOK] Event: ${event}, Action: ${action}`)

  try {
    switch (event) {
      // ─── Installation lifecycle ───
      case 'installation': {
        await handleInstallationEvent(payload)
        break
      }

      // ─── Repository access changes ───
      case 'installation_repositories': {
        await handleInstallationRepositoriesEvent(payload)
        break
      }

      // ─── Pull request events ───
      case 'pull_request': {
        await handlePullRequestEvent(payload)
        break
      }

      default:
        console.log(`[WEBHOOK] Ignoring event: ${event}`)
    }

    return NextResponse.json({ received: true })
  } catch (error: any) {
    console.error(`[WEBHOOK] Error handling ${event}:`, error.message)
    return NextResponse.json({ error: 'Processing failed' }, { status: 500 })
  }
}

// ---------------------------------------------------------------------------
// Event Handlers
// ---------------------------------------------------------------------------

async function handleInstallationEvent(payload: any) {
  const supabase = await createClient()
  const action = payload.action
  const installation = payload.installation

  if (action === 'deleted' || action === 'suspend') {
    // Remove the installation record — cascades to unlink repos
    console.log(`[WEBHOOK] Installation ${action}:`, installation.id)
    await supabase
      .from('github_installations')
      .delete()
      .eq('github_installation_id', installation.id)
    return
  }

  // For 'created' events from webhooks (not setup URL), we may not have
  // a profile_id mapping yet. The setup callback handles the initial link.
  // But we can update existing installations.
  if (action === 'created' || action === 'unsuspend') {
    console.log(`[WEBHOOK] Installation ${action}:`, installation.id)
    // Update repository_selection in case it changed
    await supabase
      .from('github_installations')
      .update({
        repository_selection: installation.repository_selection || 'all',
        github_account_login: installation.account?.login,
        updated_at: new Date().toISOString(),
      })
      .eq('github_installation_id', installation.id)
  }
}

async function handleInstallationRepositoriesEvent(payload: any) {
  const supabase = await createClient()
  const installationId = payload.installation?.id

  if (!installationId) return

  // Look up the DB installation record
  const { data: dbInstallation } = await supabase
    .from('github_installations')
    .select('id, profile_id')
    .eq('github_installation_id', installationId)
    .single()

  if (!dbInstallation) {
    console.warn('[WEBHOOK] Repo event for unknown installation:', installationId)
    return
  }

  // Full re-sync is the safest approach
  console.log('[WEBHOOK] Re-syncing repos for installation:', installationId)
  await syncInstallationRepos(installationId, dbInstallation.id, dbInstallation.profile_id)
}

async function handlePullRequestEvent(payload: any) {
  const pr = payload.pull_request
  const repoFullName = payload.repository?.full_name

  if (!pr || !repoFullName) return

  console.log(`[WEBHOOK] PR #${pr.number} ${payload.action} on ${repoFullName}`)
  await upsertPullRequest(pr, repoFullName)
}
