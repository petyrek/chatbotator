import { useEffect, useState } from "react";

export type View = "shop" | "help";

// Only "#help" selects the help page; any other hash shows the shop.
const viewFromHash = (): View =>
  window.location.hash === "#help" ? "help" : "shop";

export function useHashView() {
  const [view, setView] = useState(viewFromHash);
  useEffect(() => {
    const onHash = () => {
      setView(viewFromHash());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return view;
}
