import React from "react";
import { ShieldAlert } from "lucide-react";

export default function VulnerabilitiesPage() {
  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex items-center justify-between">
        <div>
           <h1 className="text-2xl font-medium text-gray-100 mb-1">Vulnerabilities</h1>
           <p className="text-sm text-gray-400">Dependency CVE mapping and static analysis.</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center bg-[#111318] border border-white/10 rounded-xl min-h-[500px]">
         <div className="flex flex-col items-center max-w-sm text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-6">
               <ShieldAlert size={28} className="text-red-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-200 mb-2">No Vulnerabilities Detected</h3>
            <p className="text-sm text-gray-500 mb-6">Your selected repositories are currently clear of known CVEs. Weekly comprehensive scans are scheduled automatically.</p>
         </div>
      </div>
    </div>
  );
}
