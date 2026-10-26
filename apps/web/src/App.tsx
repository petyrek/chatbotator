import { useEffect, useState } from "react";
import products from "../../../data/fixtures/products.json";
import { articles } from "./knowledge";
import { ChatWidget } from "./ChatWidget";
import { ProductArt } from "./ProductArt";

function Markdown({ content }: { content: string }) {
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

export function App() {
  const [view, setView] = useState(
    () => window.location.hash.slice(1) || "shop",
  );
  const [activeArticle, setActiveArticle] = useState("returns");
  const [apiStatus, setApiStatus] = useState<"checking" | "ready" | "offline">(
    "checking",
  );
  useEffect(() => {
    const onHash = () => {
      setView(window.location.hash.slice(1) || "shop");
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onHash);
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("API unavailable");
        const body = await response.json();
        setApiStatus(body.status === "ok" ? "ready" : "offline");
      })
      .catch((error) => {
        if (error.name !== "AbortError") setApiStatus("offline");
      });
    return () => {
      window.removeEventListener("hashchange", onHash);
      controller.abort();
    };
  }, []);
  const help = view === "help";
  const article =
    articles.find((item) => item.id === activeArticle) ?? articles[0]!;
  return (
    <>
      <a
        href="#main"
        className="skip-link"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Skip to content
      </a>
      <div className="announcement">
        A little less indoors. <span>Free EU shipping on orders €100+</span>
      </div>
      <header className="site-header">
        <a className="brand" href="#shop" aria-label="TrailSupply home">
          <svg
            width="31"
            height="28"
            viewBox="0 0 36 30"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M2 27L17 3L33 27H2Z"
              stroke="currentColor"
              strokeWidth="2.2"
            />
            <path
              d="M10 15L16 18L21 12M23 27L29 17L35 27"
              stroke="currentColor"
              strokeWidth="2"
            />
          </svg>
          TrailSupply<span className="brand-dot">®</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#shop" aria-current={!help ? "page" : undefined}>
            Shop the essentials
          </a>
          <a href="#help" aria-current={help ? "page" : undefined}>
            Help center
          </a>
        </nav>
        <span className="demo-badge">
          <span />
          Demo store
        </span>
      </header>
      <main id="main" tabIndex={-1}>
        {!help ? (
          <>
            <section className="hero">
              <div className="hero-copy">
                <p className="eyebrow">FOR THE EVERYDAY EXPLORER</p>
                <h1>
                  Good gear.
                  <br />
                  More outside.
                </h1>
                <p className="hero-description">
                  Thoughtful essentials for small escapes.
                  <br />
                  Pack light. Take the scenic route.
                </p>
                <a
                  className="primary-button"
                  href="#essentials"
                  onClick={(e) => {
                    e.preventDefault();
                    document
                      .getElementById("essentials")
                      ?.scrollIntoView({ behavior: "smooth" });
                  }}
                >
                  Find your next essential <span>↗</span>
                </a>
                <p className="hero-footnote">
                  Built for the journey. Not just the destination.
                </p>
              </div>
              <div className="landscape" aria-hidden="true">
                <svg viewBox="0 0 600 530" preserveAspectRatio="xMidYMid slice">
                  <defs>
                    <linearGradient id="sky" x2="0" y2="1">
                      <stop stopColor="#c9d4c6" />
                      <stop offset="1" stopColor="#ece7d6" />
                    </linearGradient>
                  </defs>
                  <path fill="url(#sky)" d="M0 0H600V530H0Z" />
                  <circle cx="435" cy="113" r="49" fill="#f3ead2" />
                  <path
                    d="M-30 360L160 112L327 333L425 194L650 396V530H-30Z"
                    fill="#8eaa9b"
                  />
                  <path
                    d="M160 112L113 218L158 199L190 224L203 170Z"
                    fill="#e1e4d7"
                  />
                  <path d="M425 194L395 249L422 239L451 258Z" fill="#d8dfd2" />
                  <path
                    d="M-60 480L144 260L370 470L506 292L650 400V530H-60Z"
                    fill="#587e6b"
                  />
                  <path
                    d="M-30 530Q129 336 306 430T650 413V540Z"
                    fill="#345b47"
                  />
                  <path
                    d="M-50 547Q135 412 341 510T650 480V550Z"
                    fill="#244332"
                  />
                  <path
                    d="M390 530Q285 470 303 433Q312 410 284 394"
                    fill="none"
                    stroke="#bdba91"
                    strokeWidth="10"
                    opacity=".75"
                  />
                  <g fill="#244332">
                    <path d="M52 378L75 322L99 378H86L106 404H44L65 378Z" />
                    <path d="M493 429L519 362L548 429H534L554 458H483L506 429Z" />
                  </g>
                </svg>
                <span className="landscape-label">
                  48° 09′ N &nbsp; 17° 06′ E<br />
                  ANYWHERE FEELS CLOSER OUTSIDE.
                </span>
              </div>
            </section>
            <section className="products-section" id="essentials">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">LESS, BUT BETTER</p>
                  <h2>Ready when you are.</h2>
                </div>
                <span>Three essentials. Endless possibilities.</span>
              </div>
              <div className="product-grid">
                {products.map((product, index) => (
                  <article className="product-card" key={product.id}>
                    <div className={"product-image product-image-" + index}>
                      <span className="product-index">
                        0{index + 1} / THE ESSENTIALS
                      </span>
                      <ProductArt kind={product.kind} color={product.color} />
                    </div>
                    <div className="product-meta">
                      <div>
                        <p>{product.category}</p>
                        <h3>{product.name}</h3>
                      </div>
                      <span>€{product.price}</span>
                    </div>
                    <p className="product-description">{product.description}</p>
                    <details>
                      <summary>
                        Product details <span>+</span>
                      </summary>
                      <ul>
                        {product.details.map((detail) => (
                          <li key={detail}>{detail}</li>
                        ))}
                      </ul>
                    </details>
                  </article>
                ))}
              </div>
            </section>
            <section className="help-strip">
              <div>
                <span className="small-mountain">△</span>
                <div>
                  <h2>A question before your next adventure?</h2>
                  <p>
                    Find the details on shipping, returns, and looking after
                    your gear.
                  </p>
                </div>
              </div>
              <a className="text-link" href="#help">
                Visit the help center <span>↗</span>
              </a>
            </section>
          </>
        ) : (
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
                <Markdown content={article.content} />
              </article>
            </div>
          </section>
        )}
      </main>
      <footer>
        <div>
          <a className="footer-brand" href="#shop">
            TrailSupply
          </a>
          <p>A fictional store. A real learning project.</p>
        </div>
        <div className="footer-right">
          <p>No checkout. No real orders or payments.</p>
          <p className="api-status">
            <span className={apiStatus === "ready" ? "ready" : ""} />
            {apiStatus === "ready"
              ? "API connected"
              : apiStatus === "checking"
                ? "Checking API…"
                : "API offline — storefront still available"}
          </p>
        </div>
      </footer>
      <ChatWidget />
    </>
  );
}
