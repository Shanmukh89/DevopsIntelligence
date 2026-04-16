import React from "react";
import Link from "next/link";
import { GitPullRequest, Search, CheckCircle2, AlertCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function PRReviewsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  // Fetch actual synchronized pull requests spanning all active repositories
  const { data: prs } = await supabase
    .from("pull_requests")
    .select("*, repositories(full_name)")
    .order("created_at", { ascending: false });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium text-gray-100 mb-1">PR Reviews</h1>
          <p className="text-sm text-gray-400">Automated intelligence and security scans for active pull requests.</p>
        </div>
      </div>

      <div className="bg-[#111318] border border-white/10 rounded-xl overflow-hidden text-sm">
         <div className="p-4 border-b border-white/10 bg-white/[0.02] flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
               <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={14} />
               <input type="text" placeholder="Search PRs..." className="w-full bg-white/5 border border-white/10 text-gray-300 rounded pl-9 pr-3 py-1.5 focus:outline-none focus:border-blue-500/50" />
            </div>
         </div>
         
         <div className="divide-y divide-white/5">
            {!prs || prs.length === 0 ? (
               <div className="p-16 flex flex-col items-center justify-center text-center">
                  <GitPullRequest size={48} className="text-gray-600 mb-4" />
                  <h3 className="text-gray-300 font-medium mb-1">No pull requests indexed</h3>
                  <p className="text-gray-500 max-w-sm">There are no recent pull requests for your connected repositories. Ensure you have activated them in the Import settings.</p>
               </div>
            ) : (
               prs.map(pr => (
                  <div key={pr.id} className="p-4 hover:bg-white/[0.02] transition-colors flex items-center gap-4 cursor-pointer">
                     <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center font-mono text-[10px] text-gray-400 font-bold shrink-0">
                        {pr.author.substring(0,2).toUpperCase()}
                     </div>
                     <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                           <span className="font-mono text-xs text-gray-500">#{pr.pr_number}</span>
                           <span className="truncate text-gray-200 font-medium">{pr.title}</span>
                        </div>
                        <div className="text-xs text-gray-500 flex items-center gap-2">
                           <span className="text-gray-400">{pr.repositories?.full_name}</span>
                           <span>•</span>
                           <span>{new Date(pr.created_at).toLocaleDateString()}</span>
                        </div>
                     </div>
                     <div className="flex items-center gap-3 shrink-0">
                        <div className={`px-2 py-1 rounded text-xs capitalize ${pr.status === 'open' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-purple-500/10 text-purple-400 border border-purple-500/20'}`}>
                           {pr.status}
                        </div>
                     </div>
                  </div>
               ))
            )}
         </div>
      </div>
    </div>
  );
}
