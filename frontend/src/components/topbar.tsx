"use client";

import React, { useState } from "react";
import { Search, Bell, ChevronDown, GitBranch } from "lucide-react";

const safeMockRepos = [
  { id: "repo-1", fullName: "auditr-core", language: "TypeScript", lastIndexedAt: "1h ago" },
  { id: "repo-2", fullName: "frontend-monorepo", language: "JavaScript", lastIndexedAt: "30m ago" }
];

export default function Topbar() {
  const [selectedRepo, setSelectedRepo] = useState(safeMockRepos[0]!);
  const [showRepoDropdown, setShowRepoDropdown] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);

  return (
    <header
      className="flex items-center justify-between border-b sticky top-0 z-40"
      style={{
        height: 56,
        padding: "0 32px",
        borderBottom: "1px solid var(--border-subtle)",
        backgroundColor: "rgba(10, 11, 13, 0.7)",
        backdropFilter: "blur(12px)",
      }}
    >
      {/* Repo selector */}
      <div className="relative">
        <button
          id="repo-selector"
          onClick={() => setShowRepoDropdown(!showRepoDropdown)}
          className="flex items-center gap-2 rounded-md transition-colors cursor-pointer"
          style={{
            padding: "6px 12px",
            backgroundColor: showRepoDropdown ? "var(--bg-overlay)" : "var(--bg-raised)",
            border: "1px solid var(--border-default)",
            color: "var(--text-primary)",
            fontSize: "var(--text-sm)",
            fontWeight: 500,
            transitionDuration: "var(--duration-fast)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--border-strong)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-default)"; }}
        >
          <GitBranch size={14} style={{ color: "var(--accent-500)" }} />
          <span className="font-mono" style={{ fontSize: "var(--text-sm)" }}>
            {selectedRepo.fullName}
          </span>
          <ChevronDown size={14} style={{ color: "var(--text-muted)" }} />
        </button>

        {showRepoDropdown && (
          <div
            className="absolute top-full left-0 mt-1 rounded-md shadow-lg"
            style={{
              backgroundColor: "rgba(24, 28, 35, 0.9)",
              backdropFilter: "blur(12px)",
              border: "1px solid var(--border-default)",
              boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3)",
              minWidth: 280,
              zIndex: 50,
            }}
          >
            {safeMockRepos.map((repo) => (
              <button
                key={repo.id}
                onClick={() => {
                  setSelectedRepo(repo);
                  setShowRepoDropdown(false);
                }}
                className="flex items-center gap-3 w-full text-left transition-colors cursor-pointer"
                style={{
                  padding: "10px 14px",
                  color: repo.id === selectedRepo.id ? "var(--text-primary)" : "var(--text-secondary)",
                  backgroundColor: repo.id === selectedRepo.id ? "var(--bg-subtle)" : "transparent",
                  fontSize: "var(--text-sm)",
                  border: "none",
                  transitionDuration: "var(--duration-fast)",
                }}
                onMouseEnter={(e) => { if (repo.id !== selectedRepo.id) e.currentTarget.style.backgroundColor = "var(--bg-subtle)"; }}
                onMouseLeave={(e) => { if (repo.id !== selectedRepo.id) e.currentTarget.style.backgroundColor = "transparent"; }}
              >
                <GitBranch size={14} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
                <div className="flex flex-col">
                  <span className="font-mono">{repo.fullName}</span>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {repo.language} · indexed {repo.lastIndexedAt}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right side: Search + Notifications */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div
          className="flex items-center gap-2 rounded-md transition-all"
          style={{
            padding: "6px 12px",
            backgroundColor: "var(--bg-raised)",
            border: `1px solid ${searchFocused ? "var(--accent-500)" : "var(--border-default)"}`,
            width: searchFocused ? 320 : 240,
            transitionDuration: "var(--duration-normal)",
            transitionTimingFunction: "var(--ease-expo-out)",
          }}
        >
          <Search size={14} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
          <input
            id="global-search"
            type="text"
            placeholder="Search features, repos..."
            className="bg-transparent border-none outline-none w-full"
            style={{
              color: "var(--text-primary)",
              fontSize: "var(--text-sm)",
            }}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          <kbd
            className="font-mono rounded"
            style={{
              fontSize: 10,
              padding: "1px 5px",
              backgroundColor: "var(--bg-overlay)",
              color: "var(--text-muted)",
              border: "1px solid var(--border-subtle)",
              flexShrink: 0,
            }}
          >
            ⌘K
          </kbd>
        </div>

        {/* Notification bell */}
        <button
          id="notifications-btn"
          className="relative flex items-center justify-center rounded-md transition-colors cursor-pointer"
          style={{
            width: 36,
            height: 36,
            backgroundColor: "transparent",
            border: "none",
            color: "var(--text-secondary)",
            transitionDuration: "var(--duration-fast)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-subtle)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; }}
        >
          <Bell size={18} />
          {/* Red dot for unread */}
          <span
            className="absolute rounded-full"
            style={{
              width: 7,
              height: 7,
              backgroundColor: "var(--critical)",
              top: 8,
              right: 9,
            }}
          />
        </button>
      </div>
    </header>
  );
}
