"use client";

import EmptyState from "@/components/empty-state";
import { Flame } from "lucide-react";

export default function PerformancePage() {
  return (
    <div>
      <h1
        style={{
          fontSize: "var(--text-2xl)",
          fontWeight: 500,
          color: "var(--text-primary)",
          marginBottom: 4,
        }}
      >
        Performance Traces
      </h1>
      <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", marginBottom: 16 }}>
        Distributed tracing with flame graph visualization powered by OpenTelemetry.
      </p>
      <EmptyState
        icon={Flame}
        heading="No traces collected yet"
        subtext="Add the OpenTelemetry SDK to your services and point the collector to Auditr. Traces will appear here as flame graphs once instrumented."
        ctaLabel="View Setup Guide"
        ctaHref="#"
      />
    </div>
  );
}
