"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldAlert,
  Cloud,
  Ban,
  Loader2,
  RefreshCw,
} from "lucide-react";

// Inline Github icon
const GithubIcon = ({ size = 18, className = "" }: { size?: number, className?: string }) => (
  <svg 
    viewBox="0 0 24 24" 
    width={size} 
    height={size} 
    stroke="currentColor" 
    strokeWidth="2" 
    fill="none" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from "recharts";
import MetricCard from "@/components/metric-card";
import ContentCard from "@/components/content-card";
import SeverityBadge from "@/components/severity-badge";

// ─── Custom tooltip for charts ───
function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string }>; label?: string }) {
  if (!active || !payload) return null;
  return (
    <div
      style={{
        backgroundColor: "var(--bg-overlay)",
        border: "1px solid var(--border-default)",
        borderRadius: 6,
        padding: "8px 12px",
        fontSize: "var(--text-xs)",
      }}
    >
      <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>{label}</div>
      {payload.map((entry, idx) => (
        <div key={idx} style={{ color: "var(--text-primary)" }}>
          {entry.name}: <strong>{entry.value}</strong>
        </div>
      ))}
    </div>
  );
}

function BuildStatusIcon({ status }: { status: string }) {
  switch (status) {
    case "success":
      return <CheckCircle2 size={16} style={{ color: "var(--success)" }} />;
    case "failure":
      return <XCircle size={16} style={{ color: "var(--critical)" }} />;
    case "running":
      return (
        <span className="pulse-ring inline-flex">
          <Clock size={16} style={{ color: "var(--accent-500)" }} />
        </span>
      );
    case "cancelled":
      return <Ban size={16} style={{ color: "var(--text-muted)" }} />;
    default:
      return null;
  }
}

interface DashboardViewProps {
  repositories: any[];
  pullRequests: any[];
  builds: any[];
  vulnerabilities: any[];
  costs: any[];
  hasInstallation: boolean;
  authProvider: string | null;
  anomalyTimeline: any[];
}

export default function DashboardView({
  repositories,
  pullRequests,
  builds,
  vulnerabilities,
  costs,
  hasInstallation,
  authProvider,
  anomalyTimeline
}: DashboardViewProps) {
  const [isSyncing, setIsSyncing] = useState(false);

  const appSlug = process.env.NEXT_PUBLIC_GITHUB_APP_SLUG || "auditr-dev";

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      const res = await fetch('/api/github/sync', {
        method: 'POST',
      });

      if (res.ok) {
        window.location.reload();
      } else {
        const data = await res.json();
        alert(data.error || "Sync failed. Check your GitHub App installation in Settings.");
      }
    } catch(e) {
      console.error(e);
    }
    setIsSyncing(false);
  };

  const openVulns = vulnerabilities.filter((v: any) => v.status === "open");
  const critHighVulns = openVulns.filter(
    (v: any) => v.severity === "critical" || v.severity === "high"
  );
  
  const openCosts = costs.filter((c: any) => c.status === "open");
  const totalSavings = openCosts.reduce((sum: number, c: any) => sum + Number(c.potential_saving_monthly), 0);

  // Dynamic Metrics
  const dynamicMetrics = [
    { label: "Total Repositories", value: repositories.length.toString(), change: "+0% this week", trend: "up" as const },
    { label: "Active Pull Requests", value: pullRequests.length.toString(), change: "+0% this week", trend: "up" as const },
    { label: "Open Vulnerabilities", value: openVulns.length.toString(), change: "-0% this week", trend: "down" as const },
    { label: "Potential Savings", value: `₹${totalSavings.toLocaleString("en-IN")}`, change: "0 audits today", trend: "neutral" as const },
  ];

  return (
    <div className="flex flex-col gap-8">
      {/* Page title area */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1
            style={{
              fontSize: "var(--text-2xl)",
              fontWeight: 500,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Dashboard
          </h1>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
            What needs your attention right now.
          </p>
        </div>
        
        {/* Sync Controls */}
        <div className="flex items-center gap-3">
          {hasInstallation ? (
            <button 
              onClick={handleManualSync}
              disabled={isSyncing}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-white bg-white/5 border border-white/10 rounded hover:bg-white/10 transition-colors disabled:opacity-50"
            >
              {isSyncing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Sync GitHub Data
            </button>
          ) : null}
        </div>
      </div>

      {/* GitHub App Installation Prompt */}
      {!hasInstallation && (
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-white font-medium text-base mb-1 flex items-center gap-2">
              <GithubIcon size={18} />
              {authProvider === 'github' ? 'Import your GitHub Repositories' : 'Connect your GitHub Account'}
            </h3>
            <p className="text-gray-400 text-sm m-0">
              {authProvider === 'github'
                ? 'Install the Auditr GitHub App to import your repositories, pull requests, and activity data. Your data will persist across sessions.'
                : 'Install the Auditr GitHub App to automatically import your repositories and pull requests. You can choose all or selected repos.'}
            </p>
          </div>
          <a
            href={`https://github.com/apps/${appSlug}/installations/new`}
            className="shrink-0 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm rounded-lg transition-colors disabled:opacity-75 shadow-[0_0_15px_rgba(37,99,235,0.3)]"
          >
            <GithubIcon size={16} />
            {authProvider === 'github' ? 'Import GitHub' : 'Connect GitHub'}
          </a>
        </div>
      )}

      {/* ─── 1. Metric Cards Row ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {dynamicMetrics.map((metric, idx) => (
          <MetricCard key={idx} metric={metric} />
        ))}
      </div>

      {/* ─── 2. PR Reviews + Build Activity ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Recent PR Reviews (60%) */}
        <div className="lg:col-span-3">
          <ContentCard
            title="Recent Pull Requests"
            titleRight={
              <Link href="/pr-reviews" className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium">
                View all <ArrowRight size={12} />
              </Link>
            }
            noPadding
          >
            <div>
              {pullRequests.length === 0 ? (
                 <div className="p-8 text-center text-gray-500 text-sm">
                   No pull requests found. {hasInstallation ? "Click Sync GitHub Data above." : "Connect GitHub to get started."}
                 </div>
              ) : (
                pullRequests.slice(0, 5).map((pr: any, idx: number) => (
                  <div
                    key={pr.id}
                    className="flex items-center gap-3 transition-colors cursor-pointer"
                    style={{
                      padding: "12px 16px",
                      borderBottom: idx < Math.min(pullRequests.length, 5) - 1 ? "1px solid var(--border-subtle)" : "none",
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-overlay)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
                  >
                    <div
                      className="flex items-center justify-center rounded-full font-mono shrink-0 bg-white/5 text-gray-400 text-[11px] font-semibold"
                      style={{ width: 28, height: 28 }}
                    >
                      {pr.author?.substring(0, 2).toUpperCase() || "??"}
                    </div>
  
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-gray-500">#{pr.pr_number}</span>
                        <span className="truncate text-sm text-gray-200 font-normal">{pr.title}</span>
                      </div>
                      <div className="text-[11px] text-gray-500 mt-0.5">
                        {repositories.find(r => r.id === pr.repository_id)?.name || 'Unknown Repo'} · {new Date(pr.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="px-2 py-1 bg-white/5 border border-white/10 rounded text-xs text-gray-400 capitalize">
                        {pr.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ContentCard>
        </div>

        {/* Build Activity (40%) */}
        <div className="lg:col-span-2">
          <ContentCard
            title="Build Activity — 7 days"
            titleRight={
              <Link href="/build-monitor" className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium">
                View all <ArrowRight size={12} />
              </Link>
            }
          >
            {builds.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 opacity-60">
                 <Ban className="text-gray-500 mb-2" size={32} />
                 <p className="text-gray-400 text-sm mb-1">No builds detected</p>
                 <p className="text-gray-500 text-xs text-center">Configure a CI/CD webhook to see your deployment trends.</p>
              </div>
            ) : (
                <p>Build content mapped here</p>
            )}
          </ContentCard>
        </div>
      </div>

      {/* ─── 3. Security Alerts + Cloud Cost ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Alerts */}
        <ContentCard
          title="Security Alerts"
          titleRight={
            <div className="flex items-center gap-2">
              <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
                {openVulns.length} open
              </span>
              <Link href="/vulnerabilities" className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium">
                View all <ArrowRight size={12} />
              </Link>
            </div>
          }
          noPadding
        >
          {vulnerabilities.length === 0 ? (
             <div className="p-8 text-center text-gray-500 text-sm">
                No vulnerabilities detected across active repositories.
             </div>
          ) : (
             critHighVulns.slice(0, 3).map((vuln: any, idx: number) => (
                <div key={vuln.id} className="flex items-start gap-3 p-3 border-b border-white/5">
                   <ShieldAlert size={16} className={`${vuln.severity === 'critical' ? 'text-red-500' : 'text-orange-500'} mt-0.5 shrink-0`} />
                   <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                         <span className="font-mono text-sm text-gray-200 font-medium">{vuln.package_name}</span>
                         <SeverityBadge severity={vuln.severity} />
                      </div>
                   </div>
                </div>
             ))
          )}
        </ContentCard>

        {/* Cloud Cost Recommendations */}
        <ContentCard
          title="Cloud Cost Recommendations"
          titleRight={
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-green-500 font-semibold">
                ₹{(totalSavings).toLocaleString("en-IN")}/mo saveable
              </span>
              <Link href="/cloud-costs" className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium">
                View all <ArrowRight size={12} />
              </Link>
            </div>
          }
          noPadding
        >
          {costs.length === 0 ? (
             <div className="p-8 text-center text-gray-500 text-sm">
                Connect AWS/GCP to receive infrastructure savings.
             </div>
          ) : (
             <p>Cost mappings here...</p>
          )}
        </ContentCard>
      </div>

    </div>
  );
}
