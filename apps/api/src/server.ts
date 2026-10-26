import { createServer } from "node:http";
import { handleRequest } from "./app.js";

const port = Number(process.env.PORT ?? 3001);
if (!Number.isInteger(port) || port < 1 || port > 65535)
  throw new Error("PORT must be a valid port number.");
const server = createServer(handleRequest);
server.listen(port, "127.0.0.1", () =>
  console.log("API: http://127.0.0.1:" + port + "/api/health"),
);
server.on("error", (error) => {
  console.error(error);
  process.exitCode = 1;
});
for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => {
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(1), 3000).unref();
  });
}
