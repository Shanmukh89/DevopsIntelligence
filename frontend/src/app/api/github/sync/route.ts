import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { syncInstallationRepos, syncInstallationPRs } from '@/lib/github/sync'

/**
 * Manual Sync — GitHub App Installation
 *
 * Triggered by the "Sync Now" button in the dashboard/settings.
 * Uses installation access tokens (no user OAuth token needed).
 */
export async function POST() {
  try {
    const supabase = await createClient()

    // 1. Authenticate the current user
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // 2. Look up their GitHub App installation
    const { data: installation, error: installError } = await supabase
      .from('github_installations')
      .select('id, github_installation_id')
      .eq('profile_id', user.id)
      .single()

    if (installError || !installation) {
      return NextResponse.json(
        { error: 'No GitHub App installation found. Please connect GitHub first.' },
        { status: 400 }
      )
    }

    // 3. Sync repos using installation access token
    const repos = await syncInstallationRepos(
      installation.github_installation_id,
      installation.id,
      user.id
    )

    // 4. Sync PRs for all active repos
    await syncInstallationPRs(
      installation.github_installation_id,
      installation.id
    )

    return NextResponse.json({
      success: true,
      repos_synced: repos.length,
    })
  } catch (error: any) {
    console.error('[SYNC API] Manual sync failed:', error)
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: 500 }
    )
  }
}
