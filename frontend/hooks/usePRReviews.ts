"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getPRReviews } from "@/lib/api";
import { placeholderPRReviews } from "@/lib/placeholders";
import type { PRReview } from "@/types";

export function usePRReviews(repositoryId: string | undefined) {
  const [data, setData] = useState<PRReview[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!repositoryId) {
      setLoading(false);
      setData([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const reviews = await getPRReviews(repositoryId);
      setData(reviews);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message);
      } else {
        setError("Failed to load PR reviews");
      }
      setData(placeholderPRReviews(repositoryId));
    } finally {
      setLoading(false);
    }
  }, [repositoryId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
