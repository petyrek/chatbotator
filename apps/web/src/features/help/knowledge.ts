const sources = import.meta.glob<string>("../../../../../data/knowledge/*.md", {
  eager: true,
  query: "?raw",
  import: "default",
});
export const articles = Object.entries(sources).map(([path, content]) => ({
  id: path.split("/").pop()!.replace(".md", ""),
  title: content.split("\n")[0]!.replace(/^# /, ""),
  content,
}));
