import type { ApiStatus } from "../app/useApiStatus";
import "./Footer.css";

export function Footer({ apiStatus }: { apiStatus: ApiStatus }) {
  return (
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
  );
}
