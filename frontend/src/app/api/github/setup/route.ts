import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { getInstallation } from '@/lib/github/app'
import { syncInstallationRepos, syncInstallationPRs } from '@/lib/github/sync'

/**
 * Returns the correct base URL for redirects.
 */
function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'
}

/**
 * In development, return JSON errors so we can debug.
 * In production, redirect to a page with error params.
 */
function errorResponse(message: string, details: any = {}) {
  console.error('[GITHUB SETUP ERROR]', message, details)
  // Always return visible JSON so we can see what went wrong
  return NextResponse.json(
    { error: message, details, fix: 'Check the server terminal for more details.' },
    { status: 500 }
  )
}

/**
 * GitHub App Setup Callback
 *
 * GitHub redirects here after a user installs (or reconfigures) the App.
 * We verify the installation, store the mapping, and trigger initial sync.
 */
export async function GET(request: Request) {
  const url = new URL(request.url)
  const installationId = url.searchParams.get('installation_id')
  const setupAction = url.searchParams.get('setup_action')
  const baseUrl = getBaseUrl()

  console.log('[GITHUB SETUP] ====================================')
  console.log('[GITHUB SETUP] Hit:', { installationId, setupAction, fullUrl: request.url })

  if (!installationId) {
    return errorResponse('Missing installation_id in query params')
  }

  // 1. Authenticate the current app user
  let supabase;
  try {
    supabase = await createClient()
  } catch (e: any) {
    return errorResponse('Failed to create Supabase client', { message: e.message })
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser()

  console.log('[GITHUB SETUP] Auth result:', {
    hasUser: !!user,
    userId: user?.id,
    email: user?.email,
    authError: authError?.message,
  })

  if (authError || !user) {
    return errorResponse('User not authenticated. Your session may have expired.', {
      authError: authError?.message,
      tip: 'Make sure you are logged in at http://localhost:3000 before installing the GitHub App.',
    })
  }

  // Ensure the user has a profile row (may not exist if trigger didn't fire)
  const { data: existingProfile } = await supabase
    .from('profiles')
    .select('id')
    .eq('id', user.id)
    .single()

  if (!existingProfile) {
    console.log('[GITHUB SETUP] No profile found, creating one...')
    const { error: profileError } = await supabase
      .from('profiles')
      .insert({ id: user.id, email: user.email || '' })
    if (profileError) {
      return errorResponse('Failed to create user profile', { supabaseError: profileError })
    }
  }

  // 2. Verify the installation exists on GitHub
  let ghInstallation;
  try {
    console.log('[GITHUB SETUP] Verifying installation with GitHub API...')
    ghInstallation = await getInstallation(Number(installationId))
    console.log('[GITHUB SETUP] Verified installation:', {
      id: ghInstallation.id,
      account: ghInstallation.account?.login,
      type: ghInstallation.account?.type,
      repoSelection: ghInstallation.repository_selection,
    })
  } catch (e: any) {
    return errorResponse('Failed to verify installation with GitHub API', {
      message: e.message,
      installationId,
      tip: 'This usually means the GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY is wrong.',
    })
  }

  // 3. Upsert the installation record in our database
  const installationRecord = {
    profile_id: user.id,
    github_installation_id: ghInstallation.id,
    github_account_id: ghInstallation.account?.id,
    github_account_login: ghInstallation.account?.login,
    github_account_type: ghInstallation.account?.type || 'User',
    repository_selection: ghInstallation.repository_selection || 'all',
    updated_at: new Date().toISOString(),
  }

  console.log('[GITHUB SETUP] Upserting installation:', installationRecord)

  const { data: dbInstallation, error: upsertError } = await supabase
    .from('github_installations')
    .upsert(installationRecord, { onConflict: 'github_installation_id' })
    .select('id')
    .single()

  if (upsertError || !dbInstallation) {
    return errorResponse('Failed to save installation to database', {
      supabaseError: upsertError,
      tip: 'Make sure you ran github_app_migration.sql in the Supabase SQL Editor.',
    })
  }

  console.log('[GITHUB SETUP] Installation saved. DB ID:', dbInstallation.id)

  // 4. Initial sync — fetch repos and PRs
  let syncedRepoCount = 0
  let syncError = null
  try {
    console.log('[GITHUB SETUP] Starting initial repo sync...')
    const repos = await syncInstallationRepos(
      ghInstallation.id,
      dbInstallation.id,
      user.id
    )
    syncedRepoCount = repos.length
    console.log(`[GITHUB SETUP] Synced ${syncedRepoCount} repos`)

    if (repos.length > 0) {
      console.log('[GITHUB SETUP] Starting PR sync...')
      await syncInstallationPRs(ghInstallation.id, dbInstallation.id)
      console.log('[GITHUB SETUP] PR sync done')
    }
  } catch (e: any) {
    syncError = e.message
    console.error('[GITHUB SETUP] Sync failed (non-fatal):', e.message)
  }

  console.log('[GITHUB SETUP] ✅ Complete! Redirecting to /repositories')
  console.log('[GITHUB SETUP] ====================================')

  // 5. Redirect to repositories page
  return NextResponse.redirect(`${baseUrl}/repositories`)
}
