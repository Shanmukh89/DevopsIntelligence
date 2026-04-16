import React from "react";

interface ContentCardProps {
  title: string;
  titleRight?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export default function ContentCard({
  title,
  titleRight,
  children,
  footer,
  className,
  noPadding,
}: ContentCardProps) {
  return (
    <div
      className={`rounded-xl overflow-hidden ${className || ""}`}
      style={{
        backgroundColor: "rgba(17, 19, 24, 0.7)",
        backdropFilter: "blur(12px)",
        border: "1px solid var(--border-default)",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1)",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between"
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <h3
          className="font-mono uppercase tracking-widest"
          style={{
            fontSize: "var(--text-xs)",
            color: "var(--text-muted)",
            fontWeight: 600,
            letterSpacing: "0.08em",
            margin: 0,
          }}
        >
          {title}
        </h3>
        {titleRight}
      </div>

      {/* Body */}
      <div style={{ padding: noPadding ? 0 : 16 }}>{children}</div>

      {/* Footer */}
      {footer && (
        <div
          style={{
            padding: "10px 16px",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          {footer}
        </div>
      )}
    </div>
  );
}
