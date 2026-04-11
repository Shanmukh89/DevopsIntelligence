"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getRepositories } from "@/lib/api";
import { placeholderRepositories } from "@/lib/placeholders";
import type { Repository } from "@/types";

export function useRepositories() {
  const [data, setData] = useState<Repository[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const repos = await getRepositories();
      setData(repos);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError("Failed to load repositories");
      }
      setData(placeholderRepositories);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
