"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Code, Shield, Cloud, ListTree, Activity, Settings, Zap } from "lucide-react";

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

const sections = [
  { id: "overview", title: "Platform Overview", icon: BookOpen },
  { id: "getting-started", title: "Getting Started", icon: Zap },
  { id: "authentication", title: "Authentication", icon: Shield },
  { id: "github", title: "GitHub Integration", icon: GithubIcon },
  { id: "repositories", title: "Repository Sync", icon: ListTree },
  { id: "core-features", title: "Core Features", icon: Code },
  { id: "security-costs", title: "Security & Cloud Costs", icon: Cloud },
  { id: "settings", title: "Settings & Privacy", icon: Settings },
  { id: "troubleshooting", title: "Troubleshooting & FAQ", icon: Activity },
];

export default function DocumentationHub() {
  const [activeSection, setActiveSection] = useState("overview");

  const scrollTo = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      const y = element.getBoundingClientRect().top + window.pageYOffset - 100;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  return (
    <div className="bg-[#0A0B0D] min-h-screen text-gray-300 font-sans selection:bg-blue-500/30">
      {/* Navigation */}
      <nav className="w-full border-b border-white/5 bg-[#0A0B0D]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
            <ArrowLeft size={16} />
            Back to App
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center font-mono font-bold text-white text-xs shadow-[0_0_10px_rgba(37,99,235,0.5)]">
              A
            </div>
            <span className="font-mono font-semibold tracking-tight text-white text-sm">
              docs
            </span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex items-start gap-12">
        {/* Table of Contents (Sidebar) */}
        <div className="hidden lg:block w-64 shrink-0 sticky top-28">
           <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Contents</h3>
           <nav className="flex flex-col gap-1 border-l border-white/10 pl-4">
              {sections.map((sec) => (
                 <button
                   key={sec.id}
                   onClick={() => scrollTo(sec.id)}
                   className={`flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-colors text-left ${activeSection === sec.id ? 'bg-blue-500/10 text-blue-400' : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'}`}
                 >
                   <sec.icon size={16} className={activeSection === sec.id ? 'text-blue-500' : 'text-gray-500'} />
                   {sec.title}
                 </button>
              ))}
           </nav>
        </div>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 max-w-3xl prose prose-invert prose-blue prose-headings:font-semibold prose-headings:tracking-tight prose-a:text-blue-400 hover:prose-a:text-blue-300 pb-32">
          
          <section id="overview" className="scroll-mt-28">
            <h1 className="text-4xl text-gray-100 mb-6">Auditr Documentation</h1>
            <p className="text-lg text-gray-400 leading-relaxed mb-8">
               Welcome to the official documentation for Auditr, the automated DevOps Intelligence platform. This guide covers everything from initial setup and GitHub integration to interpreting AI-driven security scans and cloud cost analytics.
            </p>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="getting-started" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100 flex items-center gap-3">Getting Started</h2>
            <p>Auditr requires <strong>zero agents</strong> out of the box for Git-based intelligence. To get started:</p>
            <ol>
               <li>Create an account using Email Magic Link or Social SSO.</li>
               <li>Navigate to <Link href="/settings">Settings</Link> to link your GitHub profile.</li>
               <li>Select the repositories you want Auditr to monitor.</li>
               <li>View insights populating on your centralized <Link href="/dashboard">Dashboard</Link>.</li>
            </ol>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="authentication" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100">Authentication</h2>
            <p>We utilize Supabase Auth under the hood to ensure secure, encrypted identity management. We support:</p>
            <ul>
               <li><strong>Magic Link (Email):</strong> Passwordless, secure entry.</li>
               <li><strong>Google OAuth:</strong> Enterprise SSO compatible.</li>
               <li><strong>GitHub OAuth:</strong> Integrated seamlessly to bootstrap repository telemetry.</li>
            </ul>
            <div className="bg-blue-900/10 border border-blue-500/20 rounded-lg p-5 not-prose mb-6">
               <h4 className="text-blue-400 font-medium text-sm mb-2">Notice for Google SSO Users</h4>
               <p className="text-blue-200/80 text-sm">If you created your account using Google, you will need to link your GitHub identity inside the Settings tab before gaining access to Code Intelligence vectors.</p>
            </div>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="github" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100 flex items-center gap-3">Connecting GitHub</h2>
            <p>During the GitHub OAuth flow, Auditr currently requests three specific scopes:</p>
            <ul>
               <li><code>repo</code>: Required to read PRs, branches, and vulnerabilities across both public and private repositories.</li>
               <li><code>read:user</code>: Required to map your GitHub identity securely.</li>
               <li><code>read:org</code>: Required to fetch repositories belonging to internal organizations you have access to.</li>
            </ul>
            <p>Your OAuth Provider tokens are stored utilizing Row Level Security (RLS) encrypted vaults and are never exposed to the client interface.</p>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="repositories" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100 flex items-center gap-3">Importing Repositories</h2>
            <p>Auditr does not automatically ingest every repository you own. This is by design to prevent hitting API rate limits on massive organizations and to maintain your precise focus.</p>
            <h3>Choosing Specific Repositories</h3>
            <p>You can manage active repositories from the <Link href="/import">Import Hub</Link>. Only repositories marked with a checkmark will trigger the background Pull Request extraction and vulnerability schedules.</p>
            <p>If you recently pushed changes to an active repository, click the <strong>Sync GitHub Data</strong> button on your dashboard to instantly refresh telemetry.</p>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="core-features" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100">Core Features</h2>
            
            <h3>PR Reviews</h3>
            <p>Our PR Review engine automatically parses differences and analyzes them against known logic faults and coding standards. Headings classify issues into specific severities.</p>
            
            <h3>Build Monitor (Coming Soon)</h3>
            <p>The Build Monitor acts as a cross-platform CI/CD visualizer. Currently in preview, this feature will soon accept webhooks directly from Jenkins, CircleCI, and GitHub Actions to map deployment reliability trends.</p>

            <h3>Code Q&A</h3>
            <p>A specialized Retrieval-Augmented Generation (RAG) system allowing you to ask natural language questions directly against your repository source tree.</p>

            <h3>Log Anomalies</h3>
            <p>Ingests Datadog, AWS CloudWatch, or raw stdout feeds to pinpoint spikes in Error/Warn rates relative to specific deployment commits.</p>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="security-costs" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100">Security & Cloud Costs</h2>
            <h3>Vulnerabilities</h3>
            <p>Utilizes abstract syntax trees to determine if vulnerable NPM packages (or standard library CVEs) are actually reachable within your local execution paths, heavily reducing notification fatigue.</p>
            <h3>Cloud Costs (Coming Soon)</h3>
            <p>Requires an IAM Read-Only role to map untagged resources and underutilized EC2/RDS instances back to their original deploying teams using Terraform State mappings.</p>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="settings" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100">Settings & Privacy</h2>
            <p>Your privacy is central to our architecture:</p>
            <ul>
               <li>Source code is <strong>never persisted</strong> on disk entirely. We keep code strictly ephemerally in-memory while generating mathematical semantic embeddings, which are then stored without the original source blocks.</li>
               <li>Sessions can be fully revoked via the Settings pane, invalidating all Next.js cookies instantly.</li>
               <li>Data freshness relies on OAuth token viability. If your syncs fail, re-authenticate your GitHub provider.</li>
            </ul>
          </section>

          <hr className="my-10 border-white/10" />

          <section id="troubleshooting" className="scroll-mt-28">
            <h2 className="text-2xl text-gray-100">Troubleshooting & FAQ</h2>
            <div className="space-y-6 mt-6">
               <div className="bg-white/[0.02] border border-white/5 p-5 rounded-lg not-prose">
                  <h4 className="font-semibold text-gray-200 mb-2">Why aren't my repositories showing up?</h4>
                  <p className="text-sm text-gray-500">If you linked an organization account, ensure you granted Third-Party Access rights for Auditr within your GitHub organization settings.</p>
               </div>
               <div className="bg-white/[0.02] border border-white/5 p-5 rounded-lg not-prose">
                  <h4 className="font-semibold text-gray-200 mb-2">Sync Data button failed?</h4>
                  <p className="text-sm text-gray-500">Your GitHub provider token may have expired. Try disconnecting and reconnecting your GitHub account from the Settings page.</p>
               </div>
            </div>
          </section>

        </main>
      </div>
    </div>
  );
}
