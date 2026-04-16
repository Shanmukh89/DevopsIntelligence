import React from "react";

type Severity = "critical" | "high" | "warning" | "info" | "clean" | "neutral";

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

const severityConfig: Record<Severity, { bg: string; color: string; label: string }> = {
  critical: { bg: "rgba(239,68,68,0.15)", color: "#EF4444", label: "CRITICAL" },
  high:     { bg: "rgba(249,115,22,0.15)", color: "#F97316", label: "HIGH" },
  warning:  { bg: "rgba(245,158,11,0.15)", color: "#F59E0B", label: "WARNING" },
  info:     { bg: "rgba(59,130,246,0.15)",  color: "#60A5FA", label: "INFO" },
  clean:    { bg: "rgba(34,197,94,0.15)",   color: "#22C55E", label: "CLEAN" },
  neutral:  { bg: "rgba(82,92,117,0.15)",   color: "#525C75", label: "NEUTRAL" },
};

export default function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const config = severityConfig[severity];

  return (
    <span
      role="status"
      className={`inline-flex items-center font-mono uppercase ${className || ""}`}
      style={{
        backgroundColor: config.bg,
        color: config.color,
        fontSize: "var(--text-xs)",
        fontWeight: 600,
        padding: "4px 8px",
        borderRadius: 9999,
        lineHeight: 1,
        letterSpacing: "0.02em",
      }}
    >
      {config.label}
    </span>
  );
}
