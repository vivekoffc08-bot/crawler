import { useState, useCallback, useRef } from 'react';
import { searchJobs, searchJobsStream } from '../api/jobs';

/**
 * Custom hook for managing job search state.
 * Supports both standard POST and SSE streaming modes.
 */
export function useJobSearch() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState({});
  const [streamMode, setStreamMode] = useState(true);
  const abortRef = useRef(null);

  const search = useCallback(async (query) => {
    // Cancel any previous search
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }

    setLoading(true);
    setError(null);
    setData(null);
    setProgress({});

    if (streamMode) {
      // SSE streaming mode — live progress
      return new Promise((resolve) => {
        const abort = searchJobsStream(query, {
          onProgress: (progressData) => {
            setProgress((prev) => ({
              ...prev,
              [progressData.source]: progressData,
            }));
          },
          onResult: (result) => {
            setData(result);
            setLoading(false);
            resolve(result);
          },
          onError: (err) => {
            if (err.source) {
              // Per-source error
              setProgress((prev) => ({
                ...prev,
                [err.source]: { ...err, status: 'error' },
              }));
            } else {
              // Global error
              setError(err.message || 'Search failed');
              setLoading(false);
              resolve(null);
            }
          },
          onDone: () => {
            setLoading(false);
          },
        });

        abortRef.current = abort;
      });
    } else {
      // Standard POST mode
      try {
        const result = await searchJobs(query);
        setData(result);
        return result;
      } catch (err) {
        setError(err.message || 'Search failed');
        return null;
      } finally {
        setLoading(false);
      }
    }
  }, [streamMode]);

  const cancel = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    setLoading(false);
  }, []);

  const reset = useCallback(() => {
    cancel();
    setData(null);
    setError(null);
    setProgress({});
  }, [cancel]);

  return {
    data,
    loading,
    error,
    progress,
    streamMode,
    setStreamMode,
    search,
    cancel,
    reset,
  };
}
