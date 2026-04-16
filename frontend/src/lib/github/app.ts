/**
 * GitHub App Authentication & API Utilities
 *
 * This module handles all server-side GitHub App operations:
 * - JWT generation for App authentication
 * - Installation access token generation
 * - Authenticated API calls
 * - Webhook signature verification
 *
 * No external dependencies — uses Node.js built-in crypto.
 */

import crypto from 'crypto'
import fs from 'fs'
import path from 'path'

// ---------------------------------------------------------------------------
// Environment helpers
// ---------------------------------------------------------------------------

function getAppId(): string {
  const id = process.env.GITHUB_APP_ID
  if (!id) throw new Error('GITHUB_APP_ID environment variable is not set')
  return id
}

function getPrivateKey(): string {
  let key: string

  // Method 1: Read from file path (most reliable)
  const keyPath = process.env.GITHUB_APP_PRIVATE_KEY_PATH
  if (keyPath) {
    const resolved = path.resolve(keyPath)
    if (fs.existsSync(resolved)) {
      console.log('[GITHUB APP] Reading private key from file:', resolved)
      key = fs.readFileSync(resolved, 'utf-8')
    } else {
      throw new Error(`GITHUB_APP_PRIVATE_KEY_PATH file not found: ${resolved}`)
    }
  } else {
    // Method 2: Inline env var with \n escape handling
    const raw = process.env.GITHUB_APP_PRIVATE_KEY
    if (!raw) {
      throw new Error('Neither GITHUB_APP_PRIVATE_KEY_PATH nor GITHUB_APP_PRIVATE_KEY is set')
    }
    key = raw.replace(/\\n/g, '\n')
  }

  // Strip Windows \r characters that corrupt PEM parsing
  key = key.replace(/\r/g, '')
  
  // Validate the key looks like a PEM
  if (!key.includes('-----BEGIN') || !key.includes('-----END')) {
    console.error('[GITHUB APP] Private key does not look like a valid PEM. First 50 chars:', key.substring(0, 50))
    throw new Error('GITHUB_APP_PRIVATE_KEY does not contain valid PEM headers')
  }
  
  return key
}

function getWebhookSecret(): string {
  const secret = process.env.GITHUB_APP_WEBHOOK_SECRET
  if (!secret) throw new Error('GITHUB_APP_WEBHOOK_SECRET environment variable is not set')
  return secret
}

// ---------------------------------------------------------------------------
// JWT Generation (RS256)
// ---------------------------------------------------------------------------

/**
 * Creates a JWT signed with the App's private key.
 * Valid for 10 minutes (GitHub's maximum).
 */
export function createAppJWT(): string {
  const now = Math.floor(Date.now() / 1000)
  const appId = getAppId()
  
  // GitHub requires `iss` to be an integer, not a string!
  const payload = {
    iat: now - 60,        // Issued 60 seconds in the past to handle clock drift
    exp: now + (10 * 60), // Expires in 10 minutes
    iss: Number(appId),   // MUST be a number per GitHub docs
  }

  console.log('[GITHUB APP] Creating JWT with iss:', payload.iss, 'iat:', payload.iat, 'exp:', payload.exp)

  const header = { alg: 'RS256', typ: 'JWT' }

  const encode = (obj: object) =>
    Buffer.from(JSON.stringify(obj)).toString('base64url')

  const headerB64 = encode(header)
  const payloadB64 = encode(payload)
  const unsigned = `${headerB64}.${payloadB64}`

  const privateKey = getPrivateKey()
  const signer = crypto.createSign('RSA-SHA256')
  signer.update(unsigned)
  const signature = signer.sign(privateKey, 'base64url')

  const jwt = `${unsigned}.${signature}`
  console.log('[GITHUB APP] JWT created successfully, length:', jwt.length)
  return jwt
}

// ---------------------------------------------------------------------------
// Installation Access Token
// ---------------------------------------------------------------------------

interface InstallationToken {
  token: string
  expires_at: string
}

/**
 * Generates a short-lived installation access token.
 * This is the primary credential used for all API calls.
 */
export async function getInstallationToken(installationId: number): Promise<InstallationToken> {
  const jwt = createAppJWT()

  const res = await fetch(
    `https://api.github.com/app/installations/${installationId}/access_tokens`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${jwt}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
    }
  )

  if (!res.ok) {
    const body = await res.text()
    console.error('[GITHUB APP] Failed to get installation token:', res.status, body)
    throw new Error(`Failed to get installation token (${res.status})`)
  }

  return res.json()
}

// ---------------------------------------------------------------------------
// Authenticated Fetch Wrapper
// ---------------------------------------------------------------------------

/**
 * Makes an authenticated API call using a GitHub App installation token.
 */
export async function githubAppFetch(
  installationId: number,
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const { token } = await getInstallationToken(installationId)

  return fetch(`https://api.github.com${path}`, {
    ...options,
    headers: {
      Authorization: `token ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(options.headers || {}),
    },
  })
}

// ---------------------------------------------------------------------------
// Installation Info
// ---------------------------------------------------------------------------

/**
 * Fetches installation details to verify it exists.
 * Uses the App JWT (not installation token) since we need app-level access.
 */
export async function getInstallation(installationId: number) {
  const jwt = createAppJWT()

  const res = await fetch(
    `https://api.github.com/app/installations/${installationId}`,
    {
      headers: {
        Authorization: `Bearer ${jwt}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
    }
  )

  if (!res.ok) {
    const body = await res.text()
    console.error('[GITHUB APP] Failed to get installation:', res.status, body)
    throw new Error(`Failed to verify installation (${res.status})`)
  }

  return res.json()
}

// ---------------------------------------------------------------------------
// Repository Fetching (paginated)
// ---------------------------------------------------------------------------

/**
 * Fetches ALL repositories accessible to the given installation.
 * Handles pagination automatically.
 */
export async function fetchInstallationRepos(installationId: number): Promise<any[]> {
  const allRepos: any[] = []
  let page = 1

  while (true) {
    const res = await githubAppFetch(
      installationId,
      `/installation/repositories?per_page=100&page=${page}`
    )

    if (!res.ok) {
      const body = await res.text()
      console.error('[GITHUB APP] Failed to fetch repos:', res.status, body)
      throw new Error(`Failed to fetch installation repositories (${res.status})`)
    }

    const data = await res.json()
    const repos = data.repositories || []
    allRepos.push(...repos)

    // Stop if we've fetched all pages
    if (allRepos.length >= data.total_count || repos.length === 0) break
    page++
  }

  return allRepos
}

// ---------------------------------------------------------------------------
// Pull Request Fetching
// ---------------------------------------------------------------------------

/**
 * Fetches recent pull requests for a specific repository.
 */
export async function fetchRepoPullRequests(
  installationId: number,
  fullName: string,
  state: 'open' | 'closed' | 'all' = 'all',
  perPage = 30
): Promise<any[]> {
  const res = await githubAppFetch(
    installationId,
    `/repos/${fullName}/pulls?state=${state}&per_page=${perPage}&sort=updated&direction=desc`
  )

  if (!res.ok) {
    console.warn(`[GITHUB APP] Failed to fetch PRs for ${fullName}:`, res.status)
    return []
  }

  return res.json()
}

// ---------------------------------------------------------------------------
// Webhook Signature Verification
// ---------------------------------------------------------------------------

/**
 * Verifies that a webhook payload was actually sent by GitHub.
 * Uses HMAC-SHA256 with the webhook secret.
 */
export function verifyWebhookSignature(payload: string, signatureHeader: string): boolean {
  const secret = getWebhookSecret()
  const expected = 'sha256=' + crypto
    .createHmac('sha256', secret)
    .update(payload, 'utf-8')
    .digest('hex')

  try {
    return crypto.timingSafeEqual(
      Buffer.from(expected),
      Buffer.from(signatureHeader)
    )
  } catch {
    return false
  }
}
