import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

/**
 * Auth Callback — Supabase PKCE Flow
 *
 * Handles the redirect after Supabase OAuth (Google/GitHub login).
 * Implements smart routing:
 *  - New user (no profile) → auto-creates profile, redirects to dashboard
 *  - Existing user → redirects to dashboard
 *  - Always backfills provider metadata (auth_provider, avatar, etc.)
 *
 * GitHub OAuth is used ONLY for identity/login, not for repo access.
 * Repo access uses the GitHub App installation model.
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const origin = requestUrl.origin

  if (!code) {
    console.error('[AUTH CALLBACK] No code in query params')
    return NextResponse.redirect(`${origin}/signin`)
  }

  const supabase = await createClient()
  const { error } = await supabase.auth.exchangeCodeForSession(code)

  if (error) {
    console.error('[AUTH CALLBACK] Session exchange failed:', error.message)
    return NextResponse.redirect(`${origin}/signin`)
  }

  // Get the authenticated user
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    console.error('[AUTH CALLBACK] No user after session exchange')
    return NextResponse.redirect(`${origin}/signin`)
  }

  // Extract provider metadata from Supabase auth
  const meta = user.user_metadata || {}
  const appMeta = user.app_metadata || {}
  const provider = appMeta.provider || null
  const providerId = meta.provider_id || meta.sub || null
  const avatarUrl = meta.avatar_url || null
  const githubUsername = meta.user_name || meta.preferred_username || null
  const fullName = meta.full_name || meta.name || ''
  const firstName = meta.first_name || fullName.split(' ')[0] || null
  const lastName = meta.last_name || fullName.split(' ').slice(1).join(' ') || null

  console.log('[AUTH CALLBACK] User authenticated:', {
    id: user.id,
    email: user.email,
    provider,
    githubUsername,
  })

  // Check if profile exists
  const { data: existingProfile } = await supabase
    .from('profiles')
    .select('id, auth_provider')
    .eq('id', user.id)
    .single()

  if (!existingProfile) {
    // No profile → auto-create (acts as signup)
    console.log('[AUTH CALLBACK] No profile found, creating one (auto-signup)...')
    const { error: insertError } = await supabase
      .from('profiles')
      .insert({
        id: user.id,
        email: user.email || '',
        first_name: firstName,
        last_name: lastName,
        avatar_url: avatarUrl,
        github_username: githubUsername,
        auth_provider: provider,
        provider_id: providerId,
      })

    if (insertError) {
      console.error('[AUTH CALLBACK] Profile creation failed:', insertError.message)
      // Don't block login — the trigger may have already created it
    } else {
      console.log('[AUTH CALLBACK] Profile created successfully')
    }
  } else {
    // Profile exists → backfill any missing metadata (avatar, provider, etc.)
    console.log('[AUTH CALLBACK] Existing profile found, backfilling metadata...')
    const updates: Record<string, string> = {}

    if (!existingProfile.auth_provider && provider) updates.auth_provider = provider
    if (avatarUrl) updates.avatar_url = avatarUrl
    if (githubUsername) updates.github_username = githubUsername
    if (firstName) updates.first_name = firstName
    if (lastName) updates.last_name = lastName
    if (providerId) updates.provider_id = providerId

    if (Object.keys(updates).length > 0) {
      updates.updated_at = new Date().toISOString()
      await supabase
        .from('profiles')
        .update(updates)
        .eq('id', user.id)
    }
  }

  // Always redirect to dashboard — it shows the appropriate GitHub import/connect prompt
  return NextResponse.redirect(`${origin}/dashboard`)
}
