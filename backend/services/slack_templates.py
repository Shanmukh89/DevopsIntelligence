"""Slack Block Kit payloads for Auditr alerts."""

from __future__ import annotations

import json
from typing import Any

from services.slack_formatting import (
    action_buttons,
    context_block,
    divider,
    now_footer_text,
    section_mrkdwn,
    severity_color,
    trackable_github_button,
)


def _so_results_lines(so_results: list[dict[str, Any]] | dict[str, Any] | None) -> str:
    if not so_results:
        return "_No Stack Overflow matches._"
    items: list[dict[str, Any]]
    if isinstance(so_results, dict):
        items = [so_results]
    else:
        items = so_results
    lines: list[str] = []
    for i, it in enumerate(items[:8], start=1):
        title = it.get("title") or it.get("question_title") or "Result"
        link = it.get("link") or it.get("url") or ""
        if link:
            lines.append(f"{i}. <{link}|{title}>")
        else:
            lines.append(f"{i}. {title}")
    if len(items) > 8:
        lines.append(f"_…and {len(items) - 8} more_")
    return "\n".join(lines) if lines else "_No Stack Overflow matches._"


def build_failure_message(
    *,
    repo_full_name: str,
    build_label: str,
    explanation: str,
    so_results: list[dict[str, Any]] | dict[str, Any] | None,
    github_url: str | None,
    auditr_url: str,
    dismiss_value: str,
    use_tracked_github_button: bool = False,
    track_base_url: str = "",
) -> dict[str, Any]:
    so_text = _so_results_lines(so_results)
    blocks: list[dict[str, Any]] = [
        section_mrkdwn(f"🔴 *Build failed* — `{repo_full_name}`\n{build_label}"),
        section_mrkdwn(f"*Explanation*\n{explanation}"),
        section_mrkdwn(f"*Stack Overflow ideas*\n{so_text}"),
        divider(),
    ]
    if use_tracked_github_button and github_url and track_base_url:
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    trackable_github_button(track_base_url=track_base_url, github_url=github_url),
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in Auditr", "emoji": True},
                        "url": auditr_url,
                        "action_id": "open_auditr",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Dismiss Alert", "emoji": True},
                        "style": "danger",
                        "action_id": "dismiss_alert",
                        "value": dismiss_value[:2000],
                    },
                ],
            }
        )
    else:
        blocks.append(
            action_buttons(
                github_url=github_url,
                auditr_url=auditr_url,
                dismiss_value=dismiss_value,
            )
        )
    blocks.append(context_block(now_footer_text()))
    return {
        "text": f"Build failed: {repo_full_name}",
        "attachments": [
            {
                "color": severity_color("critical"),
                "blocks": blocks,
            }
        ],
    }


def pr_review_message(
    *,
    repo_full_name: str,
    pr_number: int,
    pr_title: str,
    issues: list[dict[str, Any]] | str,
    github_url: str | None,
    auditr_url: str,
    dismiss_value: str,
) -> dict[str, Any]:
    if isinstance(issues, str):
        body = issues
    else:
        lines = []
        for i, issue in enumerate(issues[:15], start=1):
            sev = issue.get("severity") or "note"
            title = issue.get("title") or issue.get("message") or "Issue"
            path = issue.get("path") or issue.get("file")
            extra = f" `{path}`" if path else ""
            lines.append(f"{i}. [{sev}] {title}{extra}")
        body = "\n".join(lines) if lines else "_No issues listed._"
    blocks: list[dict[str, Any]] = [
        section_mrkdwn(f"📝 *PR review* — `{repo_full_name}` #{pr_number}\n*{pr_title}*"),
        section_mrkdwn(f"*Findings*\n{body}"),
        divider(),
        action_buttons(github_url=github_url, auditr_url=auditr_url, dismiss_value=dismiss_value),
        context_block(now_footer_text()),
    ]
    return {
        "text": f"PR review: {repo_full_name}#{pr_number}",
        "attachments": [{"color": severity_color("warning"), "blocks": blocks}],
    }


def vulnerability_message(
    *,
    repo_full_name: str,
    package_name: str,
    severity: str | None,
    cve: str | None,
    description: str | None,
    github_url: str | None,
    auditr_url: str,
    dismiss_value: str,
) -> dict[str, Any]:
    sev = (severity or "unknown").upper()
    emoji = "🛡️" if sev in ("CRITICAL", "HIGH") else "⚠️"
    detail = description or "_No description._"
    cve_line = f"*CVE / advisory:* {cve}\n" if cve else ""
    blocks: list[dict[str, Any]] = [
        section_mrkdwn(
            f"{emoji} *Vulnerability* — `{repo_full_name}`\n"
            f"*Package:* `{package_name}`  •  *Severity:* {sev}\n"
            f"{cve_line}\n{detail}"
        ),
        divider(),
        action_buttons(github_url=github_url, auditr_url=auditr_url, dismiss_value=dismiss_value),
        context_block(now_footer_text()),
    ]
    color = severity_color("critical" if sev in ("CRITICAL", "HIGH") else "warning")
    return {
        "text": f"Vulnerability: {package_name} ({repo_full_name})",
        "attachments": [{"color": color, "blocks": blocks}],
    }


def cost_spike_message(
    *,
    team_name: str,
    savings_rec: dict[str, Any],
    auditr_url: str,
    dismiss_value: str,
) -> dict[str, Any]:
    raw = json.dumps(savings_rec, indent=2)[:2900]
    blocks: list[dict[str, Any]] = [
        section_mrkdwn(f"💸 *Cloud cost warning* — team `{team_name}`\n```{raw}```"),
        divider(),
        action_buttons(github_url=None, auditr_url=auditr_url, dismiss_value=dismiss_value),
        context_block(now_footer_text()),
    ]
    return {
        "text": f"Cost warning: {team_name}",
        "attachments": [{"color": severity_color("warning"), "blocks": blocks}],
    }


def log_anomaly_message(
    *,
    repo_full_name: str,
    summary: str,
    github_url: str | None,
    auditr_url: str,
    dismiss_value: str,
) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = [
        section_mrkdwn(f"📉 *Log anomaly* — `{repo_full_name}`\n{summary}"),
        divider(),
        action_buttons(github_url=github_url, auditr_url=auditr_url, dismiss_value=dismiss_value),
        context_block(now_footer_text()),
    ]
    return {
        "text": f"Log anomaly: {repo_full_name}",
        "attachments": [{"color": severity_color("warning"), "blocks": blocks}],
    }
