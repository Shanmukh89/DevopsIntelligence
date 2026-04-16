import React from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative selection:bg-blue-500/30">
      
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-[100px]" />
      </div>

      {/* Decorative Branding Line */}
      <div className="absolute top-0 w-full h-1 bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600" />
      
      {/* Back to Home Navigation */}
      <div className="absolute top-8 left-8 z-10">
        <Link 
          href="/" 
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={16} />
          Back to home
        </Link>
      </div>

      <div className="relative z-10 w-full max-w-md px-6">
        <div className="flex flex-col items-center mb-8">
          <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center font-mono font-bold text-white text-lg shadow-[0_0_20px_rgba(37,99,235,0.4)] mb-4">
            A
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-white mb-1">
            auditr
          </h1>
        </div>

        {children}
        
      </div>
      
      <div className="mt-8 text-xs text-gray-600 font-mono text-center z-10">
        Secure authentication via OAuth
      </div>
    </div>
  );
}
