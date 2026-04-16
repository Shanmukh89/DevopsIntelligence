"use client";

import React, { useState } from "react";
import ContentCard from "@/components/content-card";
import { DatabaseZap, Play, Copy, CheckCircle2, Loader2 } from "lucide-react";

const exampleQuery = `SELECT u.name, u.email, o.total, o.created_at
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.created_at > '2024-01-01'
  AND o.status = 'completed'
ORDER BY o.total DESC;`;

export default function SQLOptimizerPage() {
  const [query, setQuery] = useState(exampleQuery);
  const [isOptimized, setIsOptimized] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [copied, setCopied] = useState(false);

  // Dynamic States from Backend
  const [optimizedQuery, setOptimizedQuery] = useState("");
  const [changeList, setChangeList] = useState<string[]>([]);
  const [indexStatements, setIndexStatements] = useState("");

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOptimize = async () => {
    if (!query.trim()) return;
    setIsOptimizing(true);
    setIsOptimized(false);
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/features/sql-optimizer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });
      
      const data = await response.json();
      setOptimizedQuery(data.rewritten_query || "Error generating query");
      setChangeList(data.explanation || ["Simplified logic."]);
      setIndexStatements(data.indexes ? data.indexes.join('\n') : "");
      setIsOptimized(true);
    } catch (error) {
      console.error("Failed to query API: ", error);
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1
          style={{
            fontSize: "var(--text-2xl)",
            fontWeight: 500,
            color: "var(--text-primary)",
            marginBottom: 4,
          }}
        >
          SQL Optimizer
        </h1>
        <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          Paste a slow SQL query and get AI-powered optimization recommendations.
        </p>
      </div>

      {/* Two-panel: Original + Optimized */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Original query */}
        <ContentCard
          title="Original Query"
          titleRight={
            <button
              onClick={handleOptimize}
              disabled={isOptimizing}
              className="flex items-center gap-1.5 rounded-md transition-colors cursor-pointer disabled:opacity-50"
              style={{
                padding: "6px 14px",
                backgroundColor: "var(--accent-500)",
                border: "none",
                color: "#fff",
                fontSize: "var(--text-xs)",
                fontWeight: 500,
                transitionDuration: "var(--duration-fast)",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-400)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-500)"; }}
            >
              {isOptimizing ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />} 
              {isOptimizing ? "Optimizing..." : "Optimize"}
            </button>
          }
        >
          <textarea
            id="sql-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full font-mono rounded-md"
            style={{
              minHeight: 200,
              padding: 14,
              backgroundColor: "var(--bg-base)",
              border: "1px solid var(--border-default)",
              color: "var(--text-secondary)",
              fontSize: 13,
              lineHeight: 1.7,
              resize: "vertical",
              outline: "none",
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-500)"; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-default)"; }}
          />
        </ContentCard>

        {/* Optimized query */}
        <ContentCard
          title="Optimized Query"
          titleRight={
            isOptimized && (
              <button
                onClick={() => handleCopy(optimizedQuery)}
                className="flex items-center gap-1 transition-colors cursor-pointer"
                style={{
                  background: "none",
                  border: "none",
                  color: copied ? "var(--success)" : "var(--text-muted)",
                  fontSize: "var(--text-xs)",
                  fontWeight: 500,
                  transitionDuration: "var(--duration-fast)",
                }}
              >
                {copied ? <CheckCircle2 size={12} /> : <Copy size={12} />}
                {copied ? "Copied" : "Copy"}
              </button>
            )
          }
        >
          {isOptimized ? (
            <pre
              className="font-mono rounded-md"
              style={{
                padding: 14,
                backgroundColor: "var(--bg-base)",
                border: "1px solid var(--border-default)",
                color: "var(--text-secondary)",
                fontSize: 13,
                lineHeight: 1.7,
                margin: 0,
                whiteSpace: "pre-wrap",
                overflowX: "auto",
              }}
            >
              {optimizedQuery}
            </pre>
          ) : (
            <div
              className="flex flex-col items-center justify-center"
              style={{ minHeight: 200, color: "var(--text-muted)" }}
            >
              {isOptimizing ? (
                <>
                  <Loader2 size={24} className="animate-spin" style={{ marginBottom: 8, color: "var(--accent-500)" }} />
                  <p style={{ fontSize: "var(--text-sm)" }}>Analyzing execution plan...</p>
                </>
              ) : (
                <>
                  <DatabaseZap size={24} style={{ marginBottom: 8 }} />
                  <p style={{ fontSize: "var(--text-sm)" }}>Click Optimize to analyze your query.</p>
                </>
              )}
            </div>
          )}
        </ContentCard>
      </div>

      {/* Dynamic Results */}
      {isOptimized && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Change list */}
            <ContentCard title="Changes Explained">
              <div className="flex flex-col gap-4">
                {changeList.map((change, idx) => (
                  <div key={idx} className="flex gap-3">
                    <span
                      className="flex items-center justify-center rounded-full font-mono flex-shrink-0"
                      style={{
                        width: 22,
                        height: 22,
                        backgroundColor: "var(--accent-glow)",
                        color: "var(--accent-400)",
                        fontSize: 11,
                        fontWeight: 600,
                      }}
                    >
                      {idx + 1}
                    </span>
                    <p
                      style={{
                        fontSize: "var(--text-sm)",
                        color: "var(--text-secondary)",
                        lineHeight: 1.6,
                        margin: 0,
                      }}
                    >
                      {change}
                    </p>
                  </div>
                ))}
              </div>
            </ContentCard>

            {/* Recommended indexes */}
            <ContentCard
              title="Recommended Indexes"
              titleRight={
                indexStatements && (
                  <button
                    onClick={() => handleCopy(indexStatements)}
                    className="flex items-center gap-1 transition-colors cursor-pointer"
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--text-muted)",
                      fontSize: "var(--text-xs)",
                      fontWeight: 500,
                      transitionDuration: "var(--duration-fast)",
                    }}
                  >
                    <Copy size={12} /> Copy
                  </button>
                )
              }
            >
              {indexStatements ? (
                <pre
                  className="font-mono rounded-md"
                  style={{
                    padding: 14,
                    backgroundColor: "var(--bg-base)",
                    border: "1px solid var(--border-default)",
                    color: "var(--success)",
                    fontSize: 13,
                    lineHeight: 1.7,
                    margin: 0,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {indexStatements}
                </pre>
              ) : (
                <p style={{color: "var(--text-muted)", fontSize: "var(--text-sm)"}}>No additional indexes needed.</p>
              )}
            </ContentCard>
          </div>
        </>
      )}
    </div>
  );
}
