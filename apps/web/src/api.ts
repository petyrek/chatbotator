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

// Mirror the models in apps/api/src/chatbotator/routes/chat.py.
export type ChatMessage = { role: "user" | "assistant"; content: string };
type ChatRequest = { messages: ChatMessage[] };
export type Citation = {
  document: string;
  title: string;
  section: string;
  quote: string;
};
export type ChatResponse = { reply: string; citations: Citation[] };

// The longest conversation the API accepts (max_length in ChatRequest).
export const MAX_CHAT_MESSAGES = 50;

// The API gives up on a turn after 60 s (TURN_DEADLINE_S in assistant/reply.py),
// so 65 s covers its worst case; after that, stop waiting.
const CHAT_TIMEOUT_MS = 65_000;

// Sends the whole conversation (the API is stateless) and returns the reply
// with the policy lines it cites.
// Throws an Error whose message is safe to show to the customer.
export async function sendChat(messages: ChatMessage[]): Promise<ChatResponse> {
  let response: Response;
  try {
    response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages } satisfies ChatRequest),
      signal: AbortSignal.timeout(CHAT_TIMEOUT_MS),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new Error(
        "The assistant took too long to answer. Please try again.",
      );
    }
    throw new Error("Can't reach the assistant. Check your connection.");
  }
  if (!response.ok) {
    // FastAPI errors look like {"detail": "..."}; validation errors (422)
    // carry a list of problems in `detail` instead of a sentence.
    const body = (await response.json().catch(() => null)) as {
      detail?: unknown;
    } | null;
    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : "Something went wrong. Please try again.",
    );
  }
  return (await response.json()) as ChatResponse;
}
