import React from "react";
export interface MetricData {
  label: string;
  value: string | number;
  delta?: string;
  deltaType?: "positive" | "negative" | "neutral";
}
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MetricCardProps {
  metric: MetricData;
}

export default function MetricCard({ metric }: MetricCardProps) {
  const deltaIcon =
    metric.deltaType === "positive" ? (
      <TrendingUp size={12} />
    ) : metric.deltaType === "negative" ? (
      <TrendingDown size={12} />
    ) : (
      <Minus size={12} />
    );

  const deltaColor =
    metric.deltaType === "positive"
      ? "var(--success)"
      : metric.deltaType === "negative"
        ? "var(--critical)"
        : "var(--text-muted)";

  return (
    <div
      className="group rounded-xl transition-all cursor-default"
      style={{
        backgroundColor: "rgba(17, 19, 24, 0.7)",
        backdropFilter: "blur(12px)",
        border: "1px solid var(--border-default)",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1)",
        padding: "20px 24px",
        transitionDuration: "var(--duration-normal)",
        transitionTimingFunction: "var(--ease-expo-out)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--border-strong)";
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = "0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border-default)";
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1)";
      }}
    >
      {/* Label */}
      <div
        className="font-mono uppercase tracking-widest"
        style={{
          fontSize: "var(--text-xs)",
          color: "var(--text-muted)",
          fontWeight: 600,
          letterSpacing: "0.08em",
          marginBottom: 8,
        }}
      >
        {metric.label}
      </div>

      {/* Large number */}
      <div
        className="font-semibold"
        style={{
          fontSize: "var(--text-3xl)",
          color: "var(--text-primary)",
          lineHeight: 1.2,
          marginBottom: 8,
        }}
      >
        {metric.value}
      </div>

      {/* Delta */}
      {metric.delta && (
        <div
          className="flex items-center gap-1"
          style={{
            fontSize: "var(--text-xs)",
            color: deltaColor,
            fontWeight: 500,
          }}
        >
          {deltaIcon}
          <span>{metric.delta}</span>
        </div>
      )}
    </div>
  );
}
