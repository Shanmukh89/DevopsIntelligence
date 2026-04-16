import React from "react";
import { Cloud } from "lucide-react";

export default function CloudCostsPage() {
  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex items-center justify-between">
        <div>
           <h1 className="text-2xl font-medium text-gray-100 mb-1">Cloud Costs</h1>
           <p className="text-sm text-gray-400">Infrastructure spending optimizations.</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center bg-[#111318] border border-white/10 rounded-xl min-h-[500px]">
         <div className="flex flex-col items-center max-w-sm text-center">
            <div className="w-16 h-16 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6">
               <Cloud size={28} className="text-blue-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-200 mb-2">Connect Cloud Provider</h3>
            <p className="text-sm text-gray-500 mb-6">Connect your AWS or GCP account in the settings to automatically calculate idle resources and saving recommendations.</p>
         </div>
      </div>
    </div>
  );
}
