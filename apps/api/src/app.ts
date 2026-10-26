import type { IncomingMessage, ServerResponse } from "node:http";

export function handleRequest(
  request: IncomingMessage,
  response: ServerResponse,
): void {
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.setHeader("Cache-Control", "no-store");
  const pathname = new URL(request.url ?? "/", "http://localhost").pathname;

  if (request.method === "GET" && pathname === "/api/health") {
    response.writeHead(200);
    response.end(
      JSON.stringify({
        status: "ok",
        service: "chatbotator-api",
        aiConnected: false,
      }),
    );
    return;
  }

  if (pathname === "/api/chat") {
    // YOUR EXERCISE: implement the first model-backed endpoint here.
    // Keep credentials on the server. Do not trust a client-supplied customer ID.
    response.writeHead(501);
    response.end(
      JSON.stringify({
        error: "NOT_IMPLEMENTED",
        message: "Your model integration starts here.",
      }),
    );
    return;
  }

  response.writeHead(404);
  response.end(JSON.stringify({ error: "NOT_FOUND" }));
}
