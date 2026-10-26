// Every call from the web app to the API lives in this file.
// The Vite dev server proxies /api to the FastAPI app on 127.0.0.1:3001.

// Mirrors the Health model in apps/api/src/chatbotator/routes/health.py.
export type Health = { status: "ok"; service: string };

export type ApiStatus = "checking" | "ready" | "offline";

export async function fetchHealth(signal: AbortSignal): Promise<Health> {
  const response = await fetch("/api/health", { signal });
  if (!response.ok) throw new Error("API unavailable");
  return (await response.json()) as Health;
}

// YOUR EXERCISE: add the chat call (POST /api/chat) and its request/response
// types here, then use it from features/chat/ChatWidget.tsx.
