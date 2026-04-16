"use client";

import React, { useState } from "react";
import ContentCard from "@/components/content-card";
import { Activity, Play, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";

interface AnomalyWindow {
  start: string;
  end: string;
  severity: string;
  description: string;
}

interface TimelinePoint {
  timestamp: string;
  reconstruction_error: number;
  threshold: number;
  is_anomaly: boolean;
  error_rate: number;
  response_time_ms: number;
  request_count: number;
  five_xx_rate: number;
}

interface DetectionResult {
  threshold: number;
  total_points: number;
  anomalies_detected: number;
  ground_truth_anomalies: number;
  anomaly_windows: AnomalyWindow[];
  timeline: TimelinePoint[];
  model_info: {
    epochs?: number;
    final_loss?: number;
    threshold?: number;
    training_sequences?: number;
    status?: string;
  };
}

export default function LogAnomaliesPage() {
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleRun = async () => {
    setIsRunning(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/features/log-anomaly-detect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ retrain: false }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Log anomaly detection failed:", error);
    } finally {
      setIsRunning(false);
    }
  };

  // Compute max reconstruction error for scaling the bar chart
  const maxError = result
    ? Math.max(...result.timeline.map((p) => p.reconstruction_error), result.threshold)
    : 1;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1
            style={{
              fontSize: "var(--text-2xl)",
              fontWeight: 500,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Log Anomaly Detection
          </h1>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
            LSTM Autoencoder-based anomaly detection on server metrics.
          </p>
        </div>
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="flex items-center gap-1.5 rounded-md transition-colors cursor-pointer disabled:opacity-50"
          style={{
            padding: "8px 16px",
            backgroundColor: "var(--accent-500)",
            border: "none",
            color: "#fff",
            fontSize: "var(--text-sm)",
            fontWeight: 500,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--accent-400)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "var(--accent-500)";
          }}
        >
          {isRunning ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Play size={16} />
          )}
          {isRunning ? "Training & Detecting..." : "Run LSTM Anomaly Detection"}
        </button>
      </div>

      {/* Loading state */}
      {isRunning && (
        <div
          className="flex flex-col items-center justify-center p-16 text-center rounded-lg"
          style={{
            backgroundColor: "var(--bg-raised)",
            border: "1px dashed var(--border-default)",
          }}
        >
          <Loader2
            size={32}
            className="animate-spin mb-4"
            style={{ color: "var(--accent-500)" }}
          />
          <p style={{ color: "var(--text-secondary)", marginBottom: 4 }}>
            Training LSTM Autoencoder on 28 days of synthetic log data...
          </p>
          <p style={{ color: "var(--text-muted)", fontSize: "var(--text-xs)" }}>
            Architecture: LSTM(64) → Bottleneck(32) → LSTM(64) | 30 epochs
          </p>
        </div>
      )}

      {/* Empty state */}
      {!result && !isRunning && (
        <div
          className="flex flex-col items-center justify-center p-20 text-center rounded-lg"
          style={{
            backgroundColor: "var(--bg-raised)",
            border: "1px solid var(--border-default)",
          }}
        >
          <Activity size={32} style={{ color: "var(--text-muted)", marginBottom: 16 }} />
          <h3 style={{ color: "var(--text-primary)", fontWeight: 500, marginBottom: 8 }}>
            No anomaly detection run yet
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)", maxWidth: 400 }}>
            Click &quot;Run LSTM Anomaly Detection&quot; to train the autoencoder on
            synthetic metrics and detect injected anomaly spikes.
          </p>
        </div>
      )}

      {/* Results */}
      {result && !isRunning && (
        <>
          {/* Model stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Anomalies Detected", value: result.anomalies_detected, color: result.anomalies_detected > 0 ? "var(--accent-500)" : "var(--success)" },
              { label: "Anomaly Threshold", value: result.threshold.toFixed(5), color: "var(--text-primary)" },
              { label: "Timeline Points", value: result.total_points, color: "var(--text-primary)" },
              { label: "Anomaly Windows", value: result.anomaly_windows.length, color: result.anomaly_windows.length > 0 ? "#ef4444" : "var(--success)" },
            ].map((stat, idx) => (
              <div
                key={idx}
                className="rounded-lg"
                style={{
                  padding: "14px 16px",
                  backgroundColor: "var(--bg-raised)",
                  border: "1px solid var(--border-default)",
                }}
              >
                <div
                  className="font-mono uppercase"
                  style={{
                    fontSize: 10,
                    color: "var(--text-muted)",
                    fontWeight: 600,
                    letterSpacing: "0.08em",
                    marginBottom: 6,
                  }}
                >
                  {stat.label}
                </div>
                <div
                  className="font-mono"
                  style={{ fontSize: "var(--text-lg)", fontWeight: 600, color: stat.color }}
                >
                  {stat.value}
                </div>
              </div>
            ))}
          </div>

          {/* Anomaly Windows */}
          {result.anomaly_windows.length > 0 && (
            <ContentCard title="Detected Anomaly Windows">
              <div className="flex flex-col gap-3">
                {result.anomaly_windows.map((window, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 rounded-lg p-3"
                    style={{
                      backgroundColor: window.severity === "critical" ? "rgba(239,68,68,0.08)" : "rgba(234,179,8,0.08)",
                      border: `1px solid ${window.severity === "critical" ? "rgba(239,68,68,0.2)" : "rgba(234,179,8,0.2)"}`,
                    }}
                  >
                    <AlertTriangle
                      size={16}
                      style={{ color: window.severity === "critical" ? "#ef4444" : "#eab308", marginTop: 2, flexShrink: 0 }}
                    />
                    <div>
                      <div style={{ fontSize: "var(--text-sm)", color: "var(--text-primary)", fontWeight: 500, marginBottom: 2 }}>
                        {new Date(window.start).toLocaleTimeString()} — {new Date(window.end).toLocaleTimeString()}
                      </div>
                      <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
                        {window.description}
                      </div>
                    </div>
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-mono uppercase ml-auto flex-shrink-0"
                      style={{
                        backgroundColor: window.severity === "critical" ? "rgba(239,68,68,0.15)" : "rgba(234,179,8,0.15)",
                        color: window.severity === "critical" ? "#ef4444" : "#eab308",
                      }}
                    >
                      {window.severity}
                    </span>
                  </div>
                ))}
              </div>
            </ContentCard>
          )}

          {/* Reconstruction Error Timeline (bar chart) */}
          <ContentCard title="Reconstruction Error Timeline">
            <div style={{ overflowX: "auto" }}>
              <div className="flex items-end gap-px" style={{ minHeight: 160, minWidth: result.timeline.length * 4 }}>
                {result.timeline.map((point, idx) => {
                  const height = Math.max((point.reconstruction_error / maxError) * 140, 2);
                  const isAnomaly = point.is_anomaly;
                  return (
                    <div
                      key={idx}
                      title={`${new Date(point.timestamp).toLocaleTimeString()}\nError: ${point.reconstruction_error.toFixed(5)}\n${isAnomaly ? "⚠ ANOMALY" : "✓ Normal"}`}
                      style={{
                        width: 3,
                        height: height,
                        backgroundColor: isAnomaly ? "#ef4444" : "var(--accent-500)",
                        opacity: isAnomaly ? 1 : 0.4,
                        borderRadius: "1px 1px 0 0",
                        flexShrink: 0,
                      }}
                    />
                  );
                })}
              </div>
              {/* Threshold line label */}
              <div className="flex justify-between mt-2">
                <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                  <span style={{ color: "var(--accent-500)" }}>■</span> Normal &nbsp;
                  <span style={{ color: "#ef4444" }}>■</span> Anomaly
                </span>
                <span className="font-mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>
                  Threshold: {result.threshold.toFixed(5)}
                </span>
              </div>
            </div>
          </ContentCard>
        </>
      )}
    </div>
  );
}
