"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Mail, ArrowRight, Loader2 } from "lucide-react";

import { createClient } from "@/lib/supabase/client";

export default function SignInPage() {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const supabase = createClient();

  const handleOAuthLogin = async (provider: 'google' | 'github') => {
    setIsLoading(provider);
    await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        scopes: provider === 'github' ? 'repo read:user read:org' : undefined
      }
    });
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading('email');
    
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/dashboard`,
      },
    });

    if (error) {
      console.error(error);
    } else {
      alert("Check your email for the login link!");
    }
    setIsLoading(null);
  };

  const GoogleIcon = () => (
    <svg viewBox="0 0 24 24" className="w-[18px] h-[18px]" aria-hidden="true" focusable="false">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );

  const GithubIcon = ({ className = "" }: { className?: string }) => (
    <svg 
      viewBox="0 0 24 24" 
      width="18" 
      height="18" 
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

  return (
    <div className="bg-[#111318]/90 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
      {/* Gloss reflection effect */}
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />

      <div className="relative z-10">
        <div className="text-center mb-8">
          <h2 className="text-xl font-medium text-white mb-2">Welcome back</h2>
          <p className="text-sm text-gray-400">Sign in to your Auditr account</p>
        </div>

        <div className="space-y-3 mb-8">
          <button
            onClick={() => handleOAuthLogin('google')}
            disabled={isLoading !== null}
            className="w-full h-11 flex items-center justify-center gap-3 bg-white text-black font-medium text-sm rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-75"
          >
            {isLoading === 'google' ? <Loader2 className="animate-spin" size={18} /> : <GoogleIcon />}
            Sign in with Google
          </button>
          <button
            onClick={() => handleOAuthLogin('github')}
            disabled={isLoading !== null}
            className="w-full h-11 flex items-center justify-center gap-3 bg-[#24292e] text-white font-medium text-sm rounded-lg hover:bg-[#1b1f23] transition-colors border border-gray-700 disabled:opacity-75"
          >
            {isLoading === 'github' ? <Loader2 className="animate-spin text-gray-400" size={18} /> : <GithubIcon />}
            Sign in with GitHub
          </button>
        </div>

        <div className="relative mb-8">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/10"></div>
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-[#111318] px-2 text-gray-500 font-mono">Or continue with logically</span>
          </div>
        </div>

        <form className="space-y-4" onSubmit={handleEmailLogin}>
          <div>
            <label htmlFor="email" className="block text-xs font-medium text-gray-400 mb-1.5 ml-1">
              Email address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail size={16} className="text-gray-500" />
              </div>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                disabled={isLoading !== null}
                className="w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 placeholder:text-gray-600 transition-all font-mono"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={isLoading !== null}
            className="w-full h-11 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm rounded-lg flex items-center justify-center gap-2 transition-colors disabled:opacity-75 shadow-[0_0_15px_rgba(37,99,235,0.3)]"
          >
            {isLoading === 'email' ? <Loader2 className="animate-spin" size={18} /> : null}
            Continue with Email
            <ArrowRight size={16} className={isLoading === 'email' ? 'hidden' : ''} />
          </button>
        </form>
      </div>

      <div className="mt-8 text-center text-sm text-gray-400 relative z-10">
        Don't have an account?{" "}
        <Link href="/signup" className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
          Sign up
        </Link>
      </div>
    </div>
  );
}
