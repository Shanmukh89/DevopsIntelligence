"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, FileCode2, Copy, Loader2, GitBranch } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: { file: string; lines: string; snippet: string }[];
}

const defaultWelcomeMessage: ChatMessage = {
  id: "m0",
  role: "assistant",
  content: "I'm here to help you! 🚀\n\nYou can ask general questions about your codebase, or select a specific repository above for in-depth questions.\n\n**Available Commands:**\n`/help` - Show available commands\n`/clear` - Clear chat history\n`/repos` - List connected repositories"
};

export default function CodeQAPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<number>(0);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  const [repositories, setRepositories] = useState<any[]>([]);
  const [selectedRepoId, setSelectedRepoId] = useState<string>("default");

  // Load state on mount
  useEffect(() => {
    const saved = localStorage.getItem("code_qa_history");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        setMessages([defaultWelcomeMessage]);
      }
    } else {
      setMessages([defaultWelcomeMessage]);
    }
    
    // Fetch repos
    const fetchRepos = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const { data } = await supabase
          .from("repositories")
          .select("id, name, full_name")
          .eq("profile_id", user.id)
          .eq("is_active", true);
        if (data) setRepositories(data);
      }
    };
    fetchRepos();
  }, []);

  // Save on messages change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem("code_qa_history", JSON.stringify(messages));
    }
  }, [messages]);

  // Handle auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Get all citations from assistant messages
  const allCitations = messages
    .filter((m) => m.role === "assistant" && m.citations)
    .flatMap((m) => m.citations || []);

  const handleCommand = (cmd: string) => {
    if (cmd === "/clear") {
      setMessages([defaultWelcomeMessage]);
      setSelectedCitation(0);
      return true;
    }
    if (cmd === "/help") {
      setMessages(prev => [...prev, {
        id: `m${Date.now()}`,
        role: "assistant",
        content: "**Available Commands:**\n\n`/help` - Show this help message\n`/clear` - Clear the current chat history\n`/repos` - View a list of your connected repositories"
      }]);
      return true;
    }
    if (cmd === "/repos") {
      const repoList = repositories.length > 0 
        ? repositories.map(r => `• **${r.full_name || r.name}**`).join("\n")
        : "No repositories connected.";
      setMessages(prev => [...prev, {
        id: `m${Date.now()}`,
        role: "assistant",
        content: `**Connected Repositories:**\n\n${repoList}`
      }]);
      return true;
    }
    return false;
  };

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isTyping) return;
    
    const userMsg: ChatMessage = {
      id: `m${Date.now()}`,
      role: "user",
      content: trimmedInput,
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    
    if (trimmedInput.startsWith("/")) {
      const isHandled = handleCommand(trimmedInput);
      if (isHandled) return;
    }

    setIsTyping(true);

    try {
      const repoName = repositories.find(r => r.id === selectedRepoId)?.full_name || null;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/features/code-qa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmedInput, repository_id: selectedRepoId, repo_full_name: repoName })
      });
      
      const data = await response.json();
      
      // Map RAG sources into the citations panel format
      const mappedCitations = (data.sources || []).map((source: any) => ({
        file: typeof source === "string" ? source : source.file || "unknown",
        lines: typeof source === "string" ? "1-50" : source.lines || "1-50",
        snippet: typeof source === "string"
          ? "// Retrieved from vector embedding search"
          : source.snippet || "// No snippet available",
      }));

      const aiMsg: ChatMessage = {
        id: `m${Date.now() + 1}`,
        role: "assistant",
        content: data.answer || "I could not generate an answer.",
        citations: mappedCitations,
      };
      
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error("QA error:", error);
      
      // We grab apiUrl again just to be safe for the error message
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      setMessages((prev) => [...prev, {
        id: `m${Date.now() + 1}`,
        role: "assistant",
        content: `Sorry, I ran into an error connecting to the FastAPI backend at **${apiUrl}**. Please check your Vercel Environment Variables.`
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleRepoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newRepoId = e.target.value;
    setSelectedRepoId(newRepoId);
    
    if (newRepoId === "default") {
      setMessages(prev => [...prev, {
        id: `m${Date.now()}`,
        role: "assistant",
        content: "You're now asking general questions across all repositories. How can I help?"
      }]);
    } else {
      const repoName = repositories.find(r => r.id === newRepoId)?.name || "the repository";
      setMessages(prev => [...prev, {
        id: `m${Date.now()}`,
        role: "assistant",
        content: `Ask questions about **${repoName}**! I'm ready.`
      }]);
    }
  };

  return (
    <div className="flex flex-col gap-6" style={{ height: "calc(100vh - 120px)" }}>
      <div className="flex items-center justify-between">
        <div>
          <h1
            style={{
              fontSize: "var(--text-2xl)",
              fontWeight: 500,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Code Q&A
          </h1>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
            Ask questions about your codebase in plain English. Powered by RAG.
          </p>
        </div>
        
        {/* Repository Selector */}
        <div className="flex items-center gap-3">
          <label htmlFor="repo-select" className="text-sm text-gray-400 font-medium">Target Repository:</label>
          <div className="relative">
            <select
              id="repo-select"
              value={selectedRepoId}
              onChange={handleRepoChange}
              className="appearance-none bg-[#1a1d24] border border-white/10 rounded-md py-2 pl-4 pr-10 text-sm text-gray-200 outline-none focus:border-blue-500/50 transition-colors cursor-pointer disabled:opacity-50 min-w-[200px]"
            >
              <option value="default">General / All Repositories</option>
              {repositories.map(repo => (
                <option key={repo.id} value={repo.id}>
                  {repo.full_name || repo.name}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-500">
              <GitBranch size={16} />
            </div>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-5 gap-6 min-h-0">
        {/* Chat thread (60%) */}
        <div
          className="lg:col-span-3 flex flex-col rounded-lg overflow-hidden"
          style={{
            backgroundColor: "var(--bg-raised)",
            border: "1px solid var(--border-default)",
          }}
        >
          {/* Messages */}
          <div className="flex-1 overflow-y-auto" style={{ padding: 16 }}>
            <div className="flex flex-col gap-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className="rounded-lg max-w-[85%]"
                    style={{
                      padding: "12px 16px",
                      backgroundColor:
                        msg.role === "user" ? "var(--bg-overlay)" : "transparent",
                      color:
                        msg.role === "user"
                          ? "var(--text-primary)"
                          : "var(--text-secondary)",
                      fontSize: "var(--text-sm)",
                      lineHeight: 1.65,
                    }}
                  >
                    {msg.content.split("\n").map((line, i) => (
                      <p key={i} style={{ margin: "4px 0", minHeight: "1lh" }}>
                        {line.split(/(\*\*.*?\*\*)/g).map((seg, j) =>
                          seg.startsWith("**") && seg.endsWith("**") ? (
                            <strong key={j} style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                              {seg.slice(2, -2)}
                            </strong>
                          ) : seg.split(/(`[^`]+`)/g).map((sub, k) =>
                            sub.startsWith("`") && sub.endsWith("`") ? (
                              <code
                                key={k}
                                className="font-mono rounded"
                                style={{
                                  fontSize: "var(--text-xs)",
                                  padding: "2px 5px",
                                  backgroundColor: "var(--bg-subtle)",
                                  color: "var(--accent-400)",
                                }}
                              >
                                {sub.slice(1, -1)}
                              </code>
                            ) : (
                              <span key={k}>{sub}</span>
                            )
                          )
                        )}
                      </p>
                    ))}

                    {/* Citation chips */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {msg.citations.map((cit, citIdx) => {
                          const globalIdx = allCitations.findIndex(
                            (c) => c.file === cit.file && c.lines === cit.lines
                          );
                          return (
                            <button
                              key={citIdx}
                              onClick={() => setSelectedCitation(globalIdx)}
                              className="flex items-center gap-1.5 rounded font-mono transition-colors cursor-pointer"
                              style={{
                                padding: "4px 8px",
                                backgroundColor:
                                  selectedCitation === globalIdx
                                    ? "var(--accent-glow)"
                                    : "var(--bg-subtle)",
                                border:
                                  selectedCitation === globalIdx
                                    ? "1px solid var(--accent-500)"
                                    : "1px solid var(--border-subtle)",
                                color: "var(--accent-400)",
                                fontSize: 11,
                                transitionDuration: "var(--duration-fast)",
                              }}
                            >
                              <FileCode2 size={11} />
                              {cit.file}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start">
                   <div className="rounded-lg max-w-[85%] flex items-center gap-2" style={{ padding: "12px 16px", color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>
                     <Loader2 size={14} className="animate-spin" />
                     Thinking...
                   </div>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>
          </div>

          {/* Input */}
          <div
            className="flex items-center gap-2"
            style={{
              padding: "12px 16px",
              borderTop: "1px solid var(--border-subtle)",
              backgroundColor: "var(--bg-overlay)",
            }}
          >
            <input
              id="code-qa-input"
              type="text"
              placeholder="Ask about your codebase... (or type /help)"
              value={input}
              disabled={isTyping}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !isTyping) {
                   e.preventDefault();
                   handleSend();
                }
              }}
              className="flex-1 bg-transparent border-none outline-none disabled:opacity-50"
              style={{
                color: "var(--text-primary)",
                fontSize: "var(--text-sm)",
              }}
            />
            <button
              id="send-message-btn"
              onClick={handleSend}
              disabled={isTyping}
              className="flex items-center justify-center rounded-md transition-colors cursor-pointer disabled:opacity-50"
              style={{
                width: 32,
                height: 32,
                backgroundColor: input.trim() && !isTyping ? "var(--accent-500)" : "var(--bg-subtle)",
                border: "none",
                color: input.trim() && !isTyping ? "#fff" : "var(--text-muted)",
                transitionDuration: "var(--duration-fast)",
              }}
            >
              <Send size={14} />
            </button>
          </div>
        </div>

        {/* Cited code panel (40%) */}
        <div
          className="lg:col-span-2 rounded-lg overflow-hidden flex flex-col"
          style={{
            backgroundColor: "var(--bg-raised)",
            border: "1px solid var(--border-default)",
          }}
        >
          <div
            className="flex items-center justify-between"
            style={{
              padding: "10px 16px",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <span
              className="font-mono uppercase tracking-widest"
              style={{
                fontSize: "var(--text-xs)",
                color: "var(--text-muted)",
                fontWeight: 600,
                letterSpacing: "0.08em",
              }}
            >
              Referenced Code
            </span>
          </div>

          <div className="flex-1 overflow-y-auto" style={{ padding: 0 }}>
            {allCitations.length > 0 && allCitations[selectedCitation] ? (
              <div>
                {/* File header */}
                <div
                  className="font-mono flex items-center justify-between"
                  style={{
                    padding: "8px 16px",
                    backgroundColor: "var(--bg-overlay)",
                    fontSize: "var(--text-xs)",
                    color: "var(--accent-400)",
                    borderBottom: "1px solid var(--border-subtle)",
                  }}
                >
                  <span>
                    {allCitations[selectedCitation].file}
                  </span>
                </div>

                {/* Code */}
                <pre
                  className="font-mono"
                  style={{
                    padding: "12px 16px",
                    fontSize: 13,
                    lineHeight: 1.7,
                    color: "var(--text-secondary)",
                    margin: 0,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {allCitations[selectedCitation].snippet}
                </pre>
              </div>
            ) : (
              <div
                className="flex flex-col items-center justify-center h-full text-center"
                style={{ padding: 32, color: "var(--text-muted)" }}
              >
                <FileCode2 size={24} style={{ marginBottom: 8 }} />
                <p style={{ fontSize: "var(--text-sm)" }}>
                  Referenced code will appear here when the AI cites specific files.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
