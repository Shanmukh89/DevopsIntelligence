"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, LayoutDashboard, ShieldAlert, Zap, Globe, GitBranch, Terminal, LineChart, Code2 } from "lucide-react";

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

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="bg-[#0A0B0D] min-h-screen text-white selection:bg-blue-500/30 overflow-x-hidden font-sans">
      
      {/* Navigation Layer */}
      <nav className={`w-full fixed top-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[#0A0B0D]/80 backdrop-blur-xl border-b border-white/5 py-3' : 'bg-transparent py-5'}`}>
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center font-mono font-bold text-white text-sm shadow-[0_0_15px_rgba(37,99,235,0.5)]">
              A
            </div>
            <span className="font-mono font-semibold tracking-tight text-white text-lg">
              auditr
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <Link href="/docs" className="hover:text-white transition-colors">How it works</Link>
          </div>
          <div className="flex items-center gap-4">
            <Link 
              href="/signin" 
              className="text-sm font-medium text-gray-400 hover:text-white transition-colors hidden sm:block"
            >
              Sign in
            </Link>
            <Link 
              href="/signup" 
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-500 transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)] hover:shadow-[0_0_25px_rgba(37,99,235,0.5)]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 lg:pt-48 lg:pb-32 px-6">
        {/* Background Gradients */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-full pointer-events-none">
          <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-blue-600/15 rounded-full blur-[120px]" />
          <div className="absolute top-[10%] left-[20%] w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-[100px]" />
        </div>

        <div className="max-w-5xl mx-auto text-center relative z-10 flex flex-col items-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-mono font-medium mb-8 uppercase tracking-widest">
            <Zap size={14} /> Intelligence Platform 2.0
          </div>
          
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-semibold tracking-tight text-white mb-8 leading-[1.05]">
            Ship code with <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">
              Zero Hesitation.
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto font-light leading-relaxed">
            Auditr is an AI-powered platform that watches your codebase, builds, security, database, and cloud — so your team can deploy with absolute confidence.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto">
            <Link 
              href="/signup" 
              className="w-full sm:w-auto px-8 py-4 text-base font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-all shadow-[0_0_20px_rgba(37,99,235,0.4)] flex items-center justify-center gap-2 group"
            >
              Start exploring
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link 
              href="/signin" 
              className="w-full sm:w-auto px-8 py-4 text-base font-medium text-white bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
            >
              <GithubIcon size={18} />
              Continue with GitHub
            </Link>
          </div>
        </div>
      </section>

      {/* Dashboard Preview Section */}
      <section className="px-6 py-12 relative z-10">
        <div className="w-full max-w-6xl mx-auto">
          <div className="rounded-xl border border-white/10 bg-[#111318]/80 backdrop-blur-xl shadow-2xl overflow-hidden relative transform transition-all duration-700 hover:scale-[1.01]">
            <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />
            
            {/* Mock Window Header */}
            <div className="h-12 border-b border-white/5 flex items-center px-4 gap-2 bg-[#0A0B0D]/50">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
            </div>

            {/* Dashboard Mock Content */}
            <div className="p-8 grid md:grid-cols-3 gap-6 bg-[#111318]">
              {/* Card 1 */}
              <div className="h-40 rounded-lg bg-white/5 border border-white/5 p-5 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <ShieldAlert size={20} className="text-red-400" />
                  <span className="text-xs font-mono text-red-400 bg-red-400/10 px-2 py-1 rounded">CRITICAL</span>
                </div>
                <div>
                  <div className="text-2xl font-semibold mb-1">0</div>
                  <div className="text-sm text-gray-400 font-mono">Open Vulnerabilities</div>
                </div>
              </div>
              {/* Card 2 */}
              <div className="h-40 rounded-lg bg-white/5 border border-white/5 p-5 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <GitBranch size={20} className="text-blue-400" />
                  <span className="text-xs font-mono text-blue-400 bg-blue-400/10 px-2 py-1 rounded">CI/CD</span>
                </div>
                <div>
                  <div className="text-2xl font-semibold mb-1">99.8%</div>
                  <div className="text-sm text-gray-400 font-mono">Build Success Rate</div>
                </div>
              </div>
              {/* Card 3 */}
              <div className="h-40 rounded-lg bg-white/5 border border-white/5 p-5 flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <Globe size={20} className="text-green-400" />
                  <span className="text-xs font-mono text-green-400 bg-green-400/10 px-2 py-1 rounded">FINOPS</span>
                </div>
                <div>
                  <div className="text-2xl font-semibold text-green-400 mb-1">-₹12,450</div>
                  <div className="text-sm text-gray-400 font-mono">Cost Optimized (Monthly)</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Detail Section */}
      <section id="features" className="py-24 px-6 relative border-t border-white/5 mt-12 bg-gradient-to-b from-transparent to-[#111318]/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-semibold mb-4">Everything your engineering team needs.</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">One unified platform to replace your fragmented dev tools.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Feature 1 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/[0.07] transition-colors">
              <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-400 mb-6">
                <Code2 size={24} />
              </div>
              <h3 className="text-xl font-medium mb-3">AI Code Q&A</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Connect your repositories and ask plain-English questions about your architecture, API routes, or legacy code. Auditr uses LLMs with direct codebase context.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/[0.07] transition-colors">
              <div className="w-12 h-12 bg-red-500/10 rounded-xl flex items-center justify-center text-red-400 mb-6">
                <Terminal size={24} />
              </div>
              <h3 className="text-xl font-medium mb-3">Log Anomalies</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Automatically swallows your production logs and surfaces statistical anomalies in real-time before your end-users actually notice there's a problem.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/[0.07] transition-colors">
              <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center text-purple-400 mb-6">
                <LineChart size={24} />
              </div>
              <h3 className="text-xl font-medium mb-3">Performance Traces</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Visualize flame-graphs and distributed traces across microservices. Stop guessing why the API is slow and pinpoint the exact database query.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/[0.07] transition-colors">
              <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center text-green-400 mb-6">
                <DatabaseZap size={24} />
              </div>
              <h3 className="text-xl font-medium mb-3">SQL Optimizer</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Auditr automatically analyzes expensive SQL queries from your ORM (Prisma, Drizzle, etc) and suggests optimized raw SQL alternatives.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6 relative overflow-hidden text-center border-t border-white/5">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
        
        <div className="max-w-3xl mx-auto relative z-10 flex flex-col items-center">
          <div className="w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center font-mono font-bold text-white text-3xl shadow-[0_0_30px_rgba(37,99,235,0.4)] mb-8">
            A
          </div>
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-6">Ready to regain control?</h2>
          <p className="text-xl text-gray-400 mb-10 font-light">Join the developers shipping faster and sleeping better.</p>
          <Link 
            href="/signup" 
            className="px-8 py-4 text-base font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-all shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)]"
          >
            Get started today
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full border-t border-white/5 py-12 px-6 bg-[#0A0B0D] relative z-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <span className="font-mono font-semibold text-gray-300">auditr</span>
            <span className="text-gray-600 text-sm">© 2026. All rights reserved.</span>
          </div>
          <div className="flex gap-6 text-sm text-gray-400">
            <Link href="/docs" className="hover:text-white transition-colors">Documentation</Link>
            <Link href="#" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link href="#" className="hover:text-white transition-colors">Terms of Service</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

const DatabaseZap = ({ size }: { size: number }) => (
  <svg 
    viewBox="0 0 24 24" 
    width={size} 
    height={size} 
    stroke="currentColor" 
    strokeWidth="2" 
    fill="none" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
  >
    <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
    <path d="M3 5V19A9 3 0 0 0 21 19V5"></path>
    <path d="M3 12A9 3 0 0 0 21 12"></path>
    <path d="M13 22l-2-7h5l-4-9"></path>
  </svg>
)
