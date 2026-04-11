# Slack integration for Auditr

This guide walks through creating a Slack app, connecting it to Auditr, and verifying notifications.

## 1. Create a Slack app

1. Open [Slack API: Your Apps](https://api.slack.com/apps) and choose **Create New App** → **From scratch**.
2. Name the app (e.g. **Auditr Alerts**) and pick a workspace for development.

## 2. OAuth & permissions

1. In the app settings, open **OAuth & Permissions**.
2. Under **Redirect URLs**, add the exact callback URL your API will use, for example:

   `http://localhost:8000/api/integrations/slack/oauth/callback`

   For production, use your public API host and HTTPS.

3. Under **Scopes** → **Bot Token Scopes**, add:

   | Scope            | Purpose                                      |
   | ---------------- | -------------------------------------------- |
   | `chat:write`     | Post messages and Block Kit payloads         |
   | `files:write`    | Upload log snippets or artifacts (optional)  |
   | `channels:read`  | List public channels for channel picker      |

   Minimal required for core alerts: `chat:write` and `channels:read`. Add `files:write` if you use file uploads.

4. **Install app** to the workspace and copy the **Bot User OAuth Token** (`xoxb-...`) only for local testing. In production, use the OAuth flow in Auditr so tokens are stored encrypted in the database.

## 3. Interactivity (Dismiss / buttons)

1. Open **Interactivity & Shortcuts** and enable **Interactivity**.
2. Set **Request URL** to:

   `https://<your-api-host>/api/integrations/slack/interactive`

3. Save changes. Slack signs requests with **Signing Secret** (see below).

## 4. Environment variables for the API

Set these in `.env` or your deployment environment:

| Variable                 | Description |
| ------------------------ | ----------- |
| `SLACK_CLIENT_ID`        | From **Basic Information** → App Credentials |
| `SLACK_CLIENT_SECRET`    | Same |
| `SLACK_SIGNING_SECRET`   | **Basic Information** → Signing Secret (verify interactive payloads) |
| `API_PUBLIC_BASE_URL`    | Public base URL of this API (for OAuth redirect and “View in GitHub” tracking links) |
| `AUDITR_DASHBOARD_URL`   | Frontend URL for “View in Auditr” buttons |
| `FERNET_KEY`             | Required in production for encrypting stored tokens (see `crypto.resolve_fernet_key`) |

Optional legacy fallback: `SLACK_BOT_TOKEN` for the synchronous `SlackClient` helper.

## 5. Connect Auditr to Slack

### Option A — Browser OAuth (recommended)

1. Call `GET /api/integrations/slack/oauth/authorize?team_id=<uuid>&redirect_uri=<encoded callback>` with a user JWT.
2. Open the returned `authorization_url` in the browser.
3. After Slack redirects to your `redirect_uri` with `code` and `state`, the API exchanges the code and stores an encrypted bot token for that team.

The `redirect_uri` must match exactly what you registered in Slack and what you pass to `authorize`.

### Option B — SPA / API `POST /api/integrations/slack/connect`

Send JSON:

```json
{
  "team_id": "<uuid>",
  "mode": "oauth",
  "code": "<from Slack redirect>",
  "redirect_uri": "https://your-api/api/integrations/slack/oauth/callback"
}
```

### Option C — Incoming webhook (simple notifications; limited interactivity)

```json
{
  "team_id": "<uuid>",
  "mode": "webhook",
  "webhook_url": "https://hooks.slack.com/services/..."
}
```

Webhook mode does not support full interactive Block Kit actions the same way as a bot; prefer OAuth for dismissible alerts.

## 6. Check status and list channels

- `GET /api/integrations/slack/status?team_id=<uuid>` — JWT required; returns whether Slack is connected.
- `GET /api/integrations/slack/channels?team_id=<uuid>` — lists channels (OAuth bot only).

## 7. Testing the connection

1. `GET /api/integrations/health/slack` — reports whether OAuth client and signing secret are configured (no secrets returned).
2. Trigger a test notification from your app by calling `SlackNotifier` methods (e.g. after a simulated build failure) or run the test suite: `pytest tests/test_slack_integration.py`.

## Security notes

- Bot tokens are encrypted at rest using Fernet (`encrypt_secret_string` / `decrypt_secret_string` in `crypto.py`).
- Logs must never print tokens or webhook URLs.
- Validate Slack signatures on `/api/integrations/slack/interactive` using `SLACK_SIGNING_SECRET`.
