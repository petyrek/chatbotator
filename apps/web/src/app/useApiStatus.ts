import { useEffect, useState } from "react";

export type ApiStatus = "checking" | "ready" | "offline";

export function useApiStatus() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("API unavailable");
        const body = await response.json();
        setApiStatus(body.status === "ok" ? "ready" : "offline");
      })
      .catch((error) => {
        if (error.name !== "AbortError") setApiStatus("offline");
      });
    return () => controller.abort();
  }, []);
  return apiStatus;
}
