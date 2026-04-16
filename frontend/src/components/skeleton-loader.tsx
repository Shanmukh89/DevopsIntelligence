import React from "react";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: number;
  className?: string;
}

export default function SkeletonLoader({
  width = "100%",
  height = 16,
  borderRadius = 4,
  className,
}: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className || ""}`}
      style={{ width, height, borderRadius }}
      aria-hidden="true"
    />
  );
}

/* Preset skeleton patterns */
export function SkeletonCard() {
  return (
    <div
      className="rounded-lg"
      style={{
        backgroundColor: "var(--bg-raised)",
        border: "1px solid var(--border-default)",
        padding: 20,
      }}
    >
      <SkeletonLoader width={100} height={10} className="mb-2" />
      <SkeletonLoader width={80} height={32} className="mb-2" />
      <SkeletonLoader width={120} height={10} />
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-3" style={{ padding: "12px 0" }}>
      <SkeletonLoader width={28} height={28} borderRadius={14} />
      <div className="flex-1 flex flex-col gap-1">
        <SkeletonLoader width="60%" height={12} />
        <SkeletonLoader width="40%" height={10} />
      </div>
      <SkeletonLoader width={60} height={20} borderRadius={10} />
    </div>
  );
}
