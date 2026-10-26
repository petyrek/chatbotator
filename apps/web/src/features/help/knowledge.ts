// Loads the policy Markdown files from data/knowledge at build time.
// The first line ("# Title") becomes `title`; the rest is `body`.
const sources = import.meta.glob<string>("@data/knowledge/*.md", {
  eager: true,
  query: "?raw",
  import: "default",
});

export const articles = Object.entries(sources).map(([path, content]) => {
  const [firstLine = "", ...rest] = content.trim().split("\n");
  return {
    id: path.split("/").pop()!.replace(".md", ""),
    title: firstLine.replace(/^# /, ""),
    body: rest.join("\n"),
  };
});
