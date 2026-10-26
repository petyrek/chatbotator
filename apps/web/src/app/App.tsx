import { Footer } from "./Footer";
import { Header } from "./Header";
import { ChatWidget } from "../features/chat/ChatWidget";
import { HelpPage } from "../features/help/HelpPage";
import { ShopPage } from "../features/shop/ShopPage";
import { useApiStatus } from "./useApiStatus";
import { useHashView } from "./useHashView";

export function App() {
  const view = useHashView();
  const apiStatus = useApiStatus();
  return (
    <>
      {/* The hash is used for page routing, so in-page links move focus
          manually instead of changing the hash (which would switch pages). */}
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
      <Header view={view} />
      <main id="main" tabIndex={-1}>
        {view === "help" ? <HelpPage /> : <ShopPage />}
      </main>
      <Footer apiStatus={apiStatus} />
      <ChatWidget />
    </>
  );
}
