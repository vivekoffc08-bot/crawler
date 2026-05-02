/**
 * API layer for communicating with the FastAPI backend.
 * Supports both standard POST and SSE streaming for live progress.
 * 
 * Set VITE_API_BASE in .env for production (e.g. https://jobhunt-api.onrender.com/api)
 */

const API_BASE = import.meta.env.VITE_API_BASE || "https://crawler-xij6.onrender.com/api";

/**
 * Search for jobs (standard POST — waits for all results).
 * @param {Object} query - JobQuery object
 * @returns {Promise<Object>} SearchResponse
 */
export const searchJobs = async (query) => {
  const response = await fetch(`${API_BASE}/jobs/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Search failed (${response.status}): ${errorText}`);
  }
  return response.json();
};

/**
 * Search for jobs with SSE streaming for live progress updates.
 * @param {Object} query - JobQuery object
 * @param {Object} callbacks - { onProgress, onResult, onError, onDone }
 * @returns {Function} abort function to cancel the stream
 */
export const searchJobsStream = (query, { onProgress, onResult, onError, onDone }) => {
  const controller = new AbortController();

  const run = async () => {
    try {
      const response = await fetch(`${API_BASE}/jobs/search/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(query),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Stream failed (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = null;
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();

            if (data === "[DONE]") {
              onDone?.();
              return;
            }

            try {
              const parsed = JSON.parse(data);

              switch (currentEvent) {
                case "progress":
                  onProgress?.(parsed);
                  break;
                case "result":
                  onResult?.(parsed);
                  break;
                case "error":
                  onError?.(parsed);
                  break;
                default:
                  // Fallback: try to determine type from data shape
                  if (parsed.source && parsed.status) {
                    onProgress?.(parsed);
                  } else if (parsed.jobs) {
                    onResult?.(parsed);
                  }
              }
            } catch (e) {
              // Skip malformed JSON
            }
            currentEvent = null;
          }
        }
      }

      onDone?.();
    } catch (err) {
      if (err.name !== "AbortError") {
        onError?.({ message: err.message });
      }
    }
  };

  run();

  return () => controller.abort();
};

/**
 * Get available job sources.
 * @returns {Promise<Object>} { sources: [...] }
 */
export const getSources = async () => {
  const response = await fetch(`${API_BASE}/jobs/sources`);
  if (!response.ok) throw new Error("Failed to fetch sources");
  return response.json();
};
