import type { ApiStatus } from "../api";
import "./Footer.css";

const statusText: Record<ApiStatus, string> = {
  checking: "Checking API…",
  ready: "API connected",
  offline: "API offline — storefront still available",
};

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
          {statusText[apiStatus]}
        </p>
      </div>
    </footer>
  );
}
