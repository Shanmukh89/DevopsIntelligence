"use client";

import React, { useState, useRef, useEffect } from "react";
import { GitBranch, Clock, Code2, ExternalLink, MoreVertical, MessageSquare, Files, DollarSign } from "lucide-react";

interface Repository {
  id: string;
  name: string;
  full_name: string;
  private: boolean;
  url: string;
  default_branch: string;
  updated_at: string;
  created_at: string;
}

export function RepositoryCard({ repo }: { repo: Repository }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleCardClick = (e: React.MouseEvent) => {
    // Ignore clicks on links or the external link icon
    if ((e.target as HTMLElement).closest('a')) {
      return;
    }
    setIsDropdownOpen(!isDropdownOpen);
  };

  return (
    <div
      key={repo.id}
      className="relative rounded-lg transition-all cursor-pointer bg-[#111318] border border-white/10 hover:border-blue-500/50 hover:scale-[1.01]"
      style={{ padding: 20 }}
      onClick={handleCardClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 pr-4">
          <GitBranch size={16} className="text-blue-500 flex-shrink-0" />
          <span className="font-mono text-sm text-gray-200 font-medium truncate">
            {repo.full_name || repo.name}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {repo.private && (
            <span className="px-1.5 py-0.5 bg-yellow-500/10 text-yellow-400 text-[10px] rounded border border-yellow-500/20 font-mono">
              private
            </span>
          )}
          <a href={repo.url} target="_blank" rel="noreferrer" className="text-gray-500 hover:text-white transition-colors" onClick={e => e.stopPropagation()}>
            <ExternalLink size={14} />
          </a>
        </div>
      </div>

      <div className="flex items-center gap-4 mt-4">
        <div className="flex items-center gap-1.5">
          <Code2 size={12} className="text-gray-500" />
          <span className="text-xs text-gray-500">
            {repo.default_branch}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
          <Clock size={11} />
          <span>Synced {new Date(repo.updated_at || repo.created_at).toLocaleDateString()}</span>
        </div>

        <div className="relative" ref={dropdownRef}>
          <button 
            className="p-1 rounded hover:bg-white/10 text-gray-400 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setIsDropdownOpen(!isDropdownOpen);
            }}
          >
            <MoreVertical size={14} />
          </button>
          
          {isDropdownOpen && (
            <div className="absolute right-0 top-full mt-2 w-56 rounded-md shadow-lg bg-[#1a1d24] ring-1 ring-black ring-opacity-5 z-10 border border-white/10 overflow-hidden">
              <div className="py-1" role="menu" aria-orientation="vertical">
                <a
                  href={`/repositories/${repo.id}/qa`}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-blue-500/10 hover:text-blue-400 transition-colors"
                  role="menuitem"
                >
                  <MessageSquare size={14} />
                  Ask questions about codebase
                </a>
                <a
                  href={`/repositories/${repo.id}/clones`}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-blue-500/10 hover:text-blue-400 transition-colors"
                  role="menuitem"
                >
                  <Files size={14} />
                  Detect code clones
                </a>
                <a
                  href={`/repositories/${repo.id}/costs`}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-blue-500/10 hover:text-blue-400 transition-colors"
                  role="menuitem"
                >
                  <DollarSign size={14} />
                  Estimate AWS costs
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
