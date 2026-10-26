export function Hero() {
  return (
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
          <path d="M160 112L113 218L158 199L190 224L203 170Z" fill="#e1e4d7" />
          <path d="M425 194L395 249L422 239L451 258Z" fill="#d8dfd2" />
          <path
            d="M-60 480L144 260L370 470L506 292L650 400V530H-60Z"
            fill="#587e6b"
          />
          <path d="M-30 530Q129 336 306 430T650 413V540Z" fill="#345b47" />
          <path d="M-50 547Q135 412 341 510T650 480V550Z" fill="#244332" />
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
  );
}
