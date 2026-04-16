"use client";

import React from "react";
import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex flex-col items-center justify-center w-full h-full min-h-[400px]">
      <Loader2 size={32} className="animate-spin mb-4" style={{ color: "var(--accent-500)" }} />
      <p style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>Loading...</p>
    </div>
  );
}
