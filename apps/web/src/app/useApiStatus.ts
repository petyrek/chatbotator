import { useEffect, useState } from "react";
import { fetchHealth, type ApiStatus } from "../api";

export function useApiStatus() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(controller.signal)
      .then((health) =>
        setApiStatus(health.status === "ok" ? "ready" : "offline"),
      )
      .catch((error) => {
        if (error.name !== "AbortError") setApiStatus("offline");
      });
    return () => controller.abort();
  }, []);
  return apiStatus;
}
