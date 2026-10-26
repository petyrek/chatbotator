import { useState } from "react";
import { articles } from "./knowledge";
import { Markdown } from "./Markdown";
import "./help.css";

export function HelpPage() {
  const [activeArticle, setActiveArticle] = useState("returns");
  const article =
    articles.find((item) => item.id === activeArticle) ?? articles[0]!;
  return (
    <section className="help-page">
      <p className="eyebrow">A LITTLE GUIDANCE</p>
      <h1>How can we help?</h1>
      <p className="help-intro">
        Straightforward answers, so you can get back outside.
      </p>
      <div className="help-layout">
        <nav aria-label="Help topics">
          {articles.map((item) => (
            <button
              key={item.id}
              aria-pressed={item.id === article.id}
              onClick={() => setActiveArticle(item.id)}
            >
              {item.title}
              <span>↗</span>
            </button>
          ))}
        </nav>
        <article className="policy-article">
          <h2>{article.title}</h2>
          <Markdown content={article.body} />
        </article>
      </div>
    </section>
  );
}
