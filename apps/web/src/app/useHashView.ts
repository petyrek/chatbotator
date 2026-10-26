import { useEffect, useState } from "react";

export function useHashView() {
  const [view, setView] = useState(
    () => window.location.hash.slice(1) || "shop",
  );
  useEffect(() => {
    const onHash = () => {
      setView(window.location.hash.slice(1) || "shop");
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return view;
}
