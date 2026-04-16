"use client";

import React, { useState } from "react";
import { User, LogOut, Shield, Loader2, ExternalLink, RefreshCw } from "lucide-react";

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

import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface Installation {
  id: string;
  github_installation_id: number;
  github_account_login: string;
  github_account_type: string;
  repository_selection: string;
  created_at: string;
  updated_at: string;
}

interface SettingsViewProps {
  user: any;
  installation: Installation | null;
  repoCount: number;
  authProvider: string | null;
}

export default function SettingsView({ user, installation, repoCount, authProvider }: SettingsViewProps) {
  const router = useRouter();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  const appSlug = process.env.NEXT_PUBLIC_GITHUB_APP_SLUG || "auditr-dev";

  const handleSignOut = async () => {
    setIsSigningOut(true);
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/signin");
  };

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncResult(null);
    try {
      const res = await fetch("/api/github/sync", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setSyncResult(`Synced ${data.repos_synced} repositories successfully.`);
        router.refresh();
      } else {
        setSyncResult(`Error: ${data.error}`);
      }
    } catch (e) {
      setSyncResult("Sync failed unexpectedly.");
    }
    setIsSyncing(false);
  };

  return (
    <div className="flex flex-col gap-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-medium text-gray-100 mb-1">Settings</h1>
        <p className="text-sm text-gray-400">Manage your connection preferences, account integrity, and session.</p>
      </div>

      {/* Profile Section */}
      <section className="bg-[#111318] border border-white/10 rounded-xl overflow-hidden">
         <div className="p-5 border-b border-white/10 flex items-center gap-3 bg-white/[0.02]">
            <User size={18} className="text-gray-400" />
            <h2 className="text-sm font-medium text-gray-200">Account Profile</h2>
         </div>
         <div className="p-6">
            <div className="grid grid-cols-[1fr_2fr] gap-6 max-w-lg">
               <div className="text-sm text-gray-500">Email Address</div>
               <div className="text-sm text-gray-200 font-medium">{user.email}</div>
               
               <div className="text-sm text-gray-500">User ID</div>
               <div className="text-sm text-gray-400 font-mono text-xs">{user.id}</div>
               
               <div className="text-sm text-gray-500">Last Signed In</div>
               <div className="text-sm text-gray-300">{new Date(user.last_sign_in_at).toLocaleString()}</div>
            </div>
         </div>
      </section>

      {/* GitHub App Integration */}
      <section className="bg-[#111318] border border-white/10 rounded-xl overflow-hidden">
         <div className="p-5 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
            <div className="flex items-center gap-3">
               <GithubIcon size={18} className="text-gray-400" />
               <h2 className="text-sm font-medium text-gray-200">GitHub App Integration</h2>
            </div>
            {installation && (
               <span className="px-2.5 py-1 rounded bg-green-500/10 text-green-400 text-xs font-medium border border-green-500/20">Connected</span>
            )}
         </div>
         <div className="p-6">
            {installation ? (
               <div className="flex flex-col gap-6">
                  {/* Installation Info */}
                  <div className="grid grid-cols-[1fr_2fr] gap-4 max-w-lg">
                     <div className="text-sm text-gray-500">GitHub Account</div>
                     <div className="text-sm text-gray-200 font-medium flex items-center gap-2">
                        <GithubIcon size={14} className="text-gray-400" />
                        {installation.github_account_login}
                        <span className="text-[10px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded font-mono">
                          {installation.github_account_type}
                        </span>
                     </div>

                     <div className="text-sm text-gray-500">Repo Access</div>
                     <div className="text-sm text-gray-300">
                        {installation.repository_selection === "all"
                          ? "All repositories"
                          : "Selected repositories"}
                     </div>

                     <div className="text-sm text-gray-500">Repositories Imported</div>
                     <div className="text-sm text-gray-300">{repoCount}</div>

                     <div className="text-sm text-gray-500">Last Synced</div>
                     <div className="text-sm text-gray-300">{new Date(installation.updated_at).toLocaleString()}</div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                     <button
                        onClick={handleSync}
                        disabled={isSyncing}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 transition-colors text-white text-sm font-medium rounded-lg flex items-center gap-2 disabled:opacity-50"
                     >
                        {isSyncing ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={14} />}
                        Sync Now
                     </button>
                     <Link
                        href="/repositories"
                        className="px-4 py-2 border border-white/10 hover:bg-white/5 transition-colors text-gray-300 text-sm font-medium rounded-lg"
                     >
                        View Repositories
                     </Link>
                     <a
                        href={`https://github.com/settings/installations/${installation.github_installation_id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-4 py-2 border border-white/10 hover:bg-white/5 transition-colors text-gray-300 text-sm font-medium rounded-lg flex items-center gap-2"
                     >
                        <ExternalLink size={14} /> Manage Installation
                     </a>
                  </div>

                  {/* Sync result feedback */}
                  {syncResult && (
                     <div className={`text-sm p-3 rounded-lg ${syncResult.startsWith("Error") ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-green-500/10 text-green-400 border border-green-500/20"}`}>
                        {syncResult}
                     </div>
                  )}
               </div>
            ) : (
               <div className="flex items-center justify-between">
                  <div>
                     <h3 className="text-gray-200 font-medium mb-1">No GitHub App Installed</h3>
                     <p className="text-sm text-gray-500 max-w-md">
                        {authProvider === 'github'
                          ? 'Install the Auditr GitHub App to import your repositories, pull requests, and activity data. Your data will persist across sessions.'
                          : 'Install the Auditr GitHub App to automatically import your repositories and pull requests. You can choose to grant access to all repositories or only specific ones.'}
                     </p>
                  </div>
                  <a
                     href={`https://github.com/apps/${appSlug}/installations/new`}
                     className="shrink-0 px-4 py-2 bg-blue-600 hover:bg-blue-500 transition-colors text-white text-sm font-medium rounded-lg flex items-center gap-2"
                  >
                     <GithubIcon size={16} />
                     {authProvider === 'github' ? 'Import GitHub' : 'Connect GitHub'}
                  </a>
               </div>
            )}
         </div>
      </section>

      {/* Security */}
      <section className="bg-[#111318] border border-white/10 rounded-xl overflow-hidden">
         <div className="p-5 border-b border-white/10 flex items-center gap-3 bg-white/[0.02]">
            <Shield size={18} className="text-gray-400" />
            <h2 className="text-sm font-medium text-gray-200">Security & Session</h2>
         </div>
         <div className="p-6">
            <div className="flex items-center justify-between">
               <div>
                  <h3 className="text-gray-200 font-medium mb-1">Active Session</h3>
                  <p className="text-sm text-gray-500">Log out of your current session across all browser windows.</p>
               </div>
               <button 
                  onClick={handleSignOut}
                  disabled={isSigningOut}
                  className="px-4 py-2 border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors text-sm font-medium rounded-lg flex items-center gap-2"
               >
                  {isSigningOut ? <Loader2 size={16} className="animate-spin" /> : <LogOut size={16} />}
                  Sign Out
               </button>
            </div>
         </div>
      </section>
    </div>
  );
}
