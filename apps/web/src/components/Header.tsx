import "./Header.css";

export function Header({ help }: { help: boolean }) {
  return (
    <>
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
    </>
  );
}
