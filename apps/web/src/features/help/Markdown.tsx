export function Markdown({ content }: { content: string }) {
  return (
    <>
      {content
        .trim()
        .split(/\n\n+/)
        .slice(1)
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
