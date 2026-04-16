import React from "react";
import { Workflow, Ban } from "lucide-react";

export default function BuildMonitorPage() {
  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex items-center justify-between">
        <div>
           <h1 className="text-2xl font-medium text-gray-100 mb-1">Build Monitor</h1>
           <p className="text-sm text-gray-400">CI/CD pipeline analysis and trace visualization.</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center bg-[#111318] border border-white/10 rounded-xl min-h-[500px]">
         <div className="flex flex-col items-center max-w-sm text-center">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-6">
               <Workflow size={28} className="text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-200 mb-2">Awaiting Ingestion Pipeline</h3>
            <p className="text-sm text-gray-500 mb-6">Build monitoring requires setting up a webhook inside your GitHub Actions or Jenkins environment. Once configured, build durations and logs will appear here.</p>
            <button className="px-6 py-2 bg-white/10 hover:bg-white/15 text-white text-sm font-medium rounded-lg transition-colors border border-white/10">View Documentation</button>
         </div>
      </div>
    </div>
  );
}
