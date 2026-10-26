// A tiny renderer for the policy files: supports only "## " headings,
// "- " bullet lists and plain paragraphs, separated by blank lines.
export function Markdown({ content }: { content: string }) {
  return (
    <>
      {content
        .trim()
        .split(/\n\n+/)
        .map((block, index) => {
          if (block.startsWith("## "))
            return <h3 key={index}>{block.slice(3)}</h3>;
          if (block.startsWith("- "))
            return (
              <ul key={index}>
                {block
                  .split("\n")
                  .filter(Boolean)
                  .map((line, i) => (
                    <li key={i}>{line.replace(/^- /, "")}</li>
                  ))}
              </ul>
            );
          return <p key={index}>{block}</p>;
        })}
    </>
  );
}
