"use client";

import React, { useState } from "react";
import EmptyState from "@/components/empty-state";
import ContentCard from "@/components/content-card";
import { Copy, Loader2, Play } from "lucide-react";

interface CloneInstance {
  file: string;
  start_line: number;
  end_line: number;
  code: string;
}

interface CloneCluster {
  cluster_id: string;
  similarity_score: number;
  instances: CloneInstance[];
  recommendation: string;
}

export default function CloneDetectorPage() {
  const [clones, setClones] = useState<CloneCluster[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [hasScanned, setHasScanned] = useState(false);

  const handleScan = async () => {
    setIsScanning(true);
    setHasScanned(false);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/features/clone-detector`);
      const data = await response.json();
      
      setClones(data.clones || []);
      setHasScanned(true);
    } catch (error) {
      console.error("Failed to fetch clones", error);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1
            style={{
              fontSize: "var(--text-2xl)",
              fontWeight: 500,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            Clone Detector
          </h1>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)"}}>
            Semantic code clone detection powered by CodeBERT embeddings.
          </p>
        </div>
        
        <button
          onClick={handleScan}
          disabled={isScanning}
          className="flex items-center gap-1.5 rounded-md transition-colors cursor-pointer disabled:opacity-50"
          style={{
            padding: "8px 16px",
            backgroundColor: "var(--accent-500)",
            border: "none",
            color: "#fff",
            fontSize: "var(--text-sm)",
            fontWeight: 500,
            transitionDuration: "var(--duration-fast)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-400)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "var(--accent-500)"; }}
        >
          {isScanning ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />} 
          {isScanning ? "Scanning repo..." : "Run ML Scan"}
        </button>
      </div>

      {!hasScanned && !isScanning ? (
        <EmptyState
          icon={Copy}
          heading="No clones scanned yet"
          subtext="Run a scan to detect duplicate code across your codebase using ML-powered semantic analysis."
        />
      ) : isScanning ? (
        <div className="flex flex-col items-center justify-center p-20 text-center rounded-lg" style={{backgroundColor: "var(--bg-raised)", border: "1px dashed var(--border-default)"}}>
           <Loader2 size={32} className="animate-spin text-blue-500 mb-4" style={{color: "var(--accent-500)"}} />
           <p style={{color: "var(--text-secondary)"}}>Computing CodeBERT cosine similarity matrix...</p>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {clones.map((cluster) => (
            <ContentCard 
              key={cluster.cluster_id}
              title={`Similarity: ${(cluster.similarity_score * 100).toFixed(0)}%`}
              titleRight={<span style={{fontSize: 12, color: "var(--text-muted)"}}>Cluster {cluster.cluster_id}</span>}
            >
              <div className="flex flex-col gap-4">
                <div style={{padding: 12, backgroundColor: "var(--accent-glow)", border: "1px solid var(--accent-500)", borderRadius: 8, color: "var(--text-primary)", fontSize: "var(--text-sm)"}}>
                  <strong style={{color: "var(--accent-400)"}}>AI Recommendation:</strong> {cluster.recommendation}
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {cluster.instances.map((instance, idx) => (
                    <div key={idx} className="flex flex-col border rounded-md overflow-hidden" style={{borderColor: "var(--border-subtle)"}}>
                       <div className="font-mono flex justify-between px-3 py-2 text-xs" style={{backgroundColor: "var(--bg-overlay)", borderBottom: "1px solid var(--border-subtle)", color: "var(--text-secondary)"}}>
                          <span>{instance.file}</span>
                          <span>Lines {instance.start_line}-{instance.end_line}</span>
                       </div>
                       <pre className="font-mono p-3 m-0 text-xs text-gray-300 overflow-x-auto" style={{backgroundColor: "var(--bg-base)"}}>
                          {instance.code}
                       </pre>
                    </div>
                  ))}
                </div>
              </div>
            </ContentCard>
          ))}
        </div>
      )}
    </div>
  );
}
