"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  GitBranch,
  GitPullRequest,
  MessageSquareCode,
  Copy,
  FileText,
  Workflow,
  Activity,
  Flame,
  ShieldAlert,
  DatabaseZap,
  Cloud,
  Settings,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Command,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    label: "OVERVIEW",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Repositories", href: "/repositories", icon: GitBranch },
    ],
  },
  {
    label: "CODE INTELLIGENCE",
    items: [
      { label: "PR Reviews", href: "/pr-reviews", icon: GitPullRequest },
      { label: "Code Q&A", href: "/code-qa", icon: MessageSquareCode },
      { label: "Clone Detector", href: "/clone-detector", icon: Copy },
    ],
  },
  {
    label: "OPERATIONS",
    items: [
      { label: "Build Monitor", href: "/build-monitor", icon: Workflow },
      { label: "Log Anomalies", href: "/log-anomalies", icon: Activity },
      { label: "Performance Traces", href: "/performance", icon: Flame },
    ],
  },
  {
    label: "SECURITY & COST",
    items: [
      { label: "Vulnerabilities", href: "/vulnerabilities", icon: ShieldAlert },
      { label: "SQL Optimizer", href: "/sql-optimizer", icon: DatabaseZap },
      { label: "Cloud Costs", href: "/cloud-costs", icon: Cloud },
    ],
  },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <aside
      className="desktop-only flex flex-col border-r h-screen sticky top-0 transition-all overflow-hidden"
      style={{
        width: collapsed ? 56 : 240,
        minWidth: collapsed ? 56 : 240,
        borderRight: "1px solid var(--border-subtle)",
        backgroundColor: "rgba(10, 11, 13, 0.7)",
        backdropFilter: "blur(12px)",
        transitionDuration: "var(--duration-normal)",
        transitionTimingFunction: "var(--ease-expo-out)",
      }}
    >
      {/* Logo */}
      <div
        className="flex items-center gap-2 border-b"
        style={{
          height: 56,
          padding: collapsed ? "0 16px" : "0 20px",
          borderColor: "var(--border-subtle)",
        }}
      >
        <div
          className="flex items-center justify-center rounded font-mono font-bold"
          style={{
            width: 28,
            height: 28,
            backgroundColor: "var(--accent-500)",
            color: "#fff",
            fontSize: "var(--text-sm)",
          }}
        >
          A
        </div>
        {!collapsed && (
          <span
            className="font-mono font-semibold tracking-tight"
            style={{ color: "var(--text-primary)", fontSize: "var(--text-lg)" }}
          >
            auditr
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2" style={{ padding: "8px 0" }}>
        {navSections.map((section) => (
          <div key={section.label} style={{ marginBottom: 8 }}>
            {!collapsed && (
              <div
                className="font-mono uppercase tracking-widest"
                style={{
                  fontSize: "var(--text-xs)",
                  color: "var(--text-muted)",
                  padding: "8px 20px 4px",
                  fontWeight: 600,
                  letterSpacing: "0.08em",
                }}
              >
                {section.label}
              </div>
            )}
            {section.items.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 relative transition-colors"
                  style={{
                    padding: collapsed ? "8px 18px" : "8px 20px",
                    color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                    backgroundColor: isActive ? "var(--bg-subtle)" : "transparent",
                    fontSize: "var(--text-sm)",
                    fontWeight: isActive ? 500 : 400,
                    transitionDuration: "var(--duration-fast)",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = "var(--bg-subtle)";
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <div
                      className="absolute left-0 top-1/2 -translate-y-1/2 rounded-r"
                      style={{
                        width: 3,
                        height: 20,
                        backgroundColor: "var(--accent-500)",
                        boxShadow: "0 0 8px var(--accent-glow)",
                      }}
                    />
                  )}
                  <Icon size={18} style={{ flexShrink: 0 }} />
                  {!collapsed && (
                    <>
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.badge !== undefined && (
                        <span
                          className="flex items-center justify-center rounded-full font-mono"
                          style={{
                            minWidth: 20,
                            height: 20,
                            fontSize: 11,
                            fontWeight: 600,
                            backgroundColor: "var(--accent-glow)",
                            color: "var(--accent-400)",
                            padding: "0 6px",
                          }}
                        >
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Bottom section */}
      <div
        className="border-t flex flex-col gap-1"
        style={{
          borderColor: "var(--border-subtle)",
          padding: collapsed ? "8px 0" : "8px 0",
        }}
      >
        <Link
          href="/settings"
          className="flex items-center gap-3 transition-colors"
          style={{
            padding: collapsed ? "8px 18px" : "8px 20px",
            color: "var(--text-secondary)",
            fontSize: "var(--text-sm)",
            transitionDuration: "var(--duration-fast)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-subtle)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
        >
          <Settings size={18} />
          {!collapsed && <span>Settings</span>}
        </Link>


        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-3 transition-colors cursor-pointer"
          style={{
            padding: collapsed ? "8px 18px" : "8px 20px",
            color: "var(--text-muted)",
            fontSize: "var(--text-sm)",
            background: "none",
            border: "none",
            width: "100%",
            textAlign: "left",
            transitionDuration: "var(--duration-fast)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-secondary)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)"; }}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!collapsed && (
            <span className="flex items-center gap-2">
              Collapse
              <kbd
                className="flex items-center gap-0.5 rounded font-mono"
                style={{
                  fontSize: 10,
                  padding: "2px 4px",
                  backgroundColor: "var(--bg-overlay)",
                  color: "var(--text-muted)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <Command size={10} />B
              </kbd>
            </span>
          )}
        </button>
      </div>
    </aside>
  );
}
