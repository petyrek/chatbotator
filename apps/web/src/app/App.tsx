import { Footer } from "../components/Footer";
import { Header } from "../components/Header";
import { ChatWidget } from "../features/chat/ChatWidget";
import { HelpPage } from "../features/help/HelpPage";
import { ShopPage } from "../features/shop/ShopPage";
import { useApiStatus } from "./useApiStatus";
import { useHashView } from "./useHashView";

export function App() {
  const view = useHashView();
  const apiStatus = useApiStatus();
  const help = view === "help";
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
      <Header help={help} />
      <main id="main" tabIndex={-1}>
        {help ? <HelpPage /> : <ShopPage />}
      </main>
      <Footer apiStatus={apiStatus} />
      <ChatWidget />
    </>
  );
}
