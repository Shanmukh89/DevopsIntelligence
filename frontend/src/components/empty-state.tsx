"use client";

import React from "react";

interface EmptyStateProps {
  icon: React.ElementType;
  heading: string;
  subtext: string;
  ctaLabel?: string;
  ctaHref?: string;
}

export default function EmptyState({
  icon: Icon,
  heading,
  subtext,
  ctaLabel,
  ctaHref,
}: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center text-center"
      style={{ paddingTop: 64 }}
    >
      <Icon size={32} style={{ color: "var(--text-muted)", marginBottom: 16 }} />
      <h2
        style={{
          fontSize: "var(--text-xl)",
          color: "var(--text-primary)",
          fontWeight: 500,
          marginBottom: 8,
        }}
      >
        {heading}
      </h2>
      <p
        style={{
          fontSize: "var(--text-base)",
          color: "var(--text-secondary)",
          maxWidth: 400,
          marginBottom: ctaLabel ? 24 : 0,
        }}
      >
        {subtext}
      </p>
      {ctaLabel && ctaHref && (
        <a
          href={ctaHref}
          className="inline-flex items-center justify-center rounded-md transition-colors"
          style={{
            padding: "8px 16px",
            backgroundColor: "var(--accent-500)",
            color: "#fff",
            fontSize: "var(--text-sm)",
            fontWeight: 500,
            textDecoration: "none",
            transitionDuration: "var(--duration-fast)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-400)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-500)"; }}
        >
          {ctaLabel}
        </a>
      )}
    </div>
  );
}
