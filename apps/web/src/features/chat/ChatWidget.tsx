import { useEffect, useRef, useState, type FormEvent } from "react";
import "./chat.css";

type Message = { id: string; role: "assistant" | "user"; text: string };

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: crypto.randomUUID(),
      role: "assistant",
      text: "Hi there. This is the chat preview. AI answers are your next exercise; the published policies are ready in the help center.",
    },
  ]);
  const input = useRef<HTMLInputElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);
  useEffect(() => {
    if (open) bottom.current?.scrollIntoView({ block: "nearest" });
  }, [messages, open]);

  function close() {
    setOpen(false);
    launcher.current?.focus();
  }

  function send(event: FormEvent) {
    event.preventDefault();
    const question = text.trim();
    if (!question) return;
    // YOUR EXERCISE: replace this local preview with a call to your API
    // (add the request function to src/api.ts).
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", text: question },
      {
        id: crypto.randomUUID(),
        role: "assistant",
        text: "Preview only — no model or retrieval is connected yet. Open the help center to read the store policies.",
      },
    ]);
    setText("");
    input.current?.focus();
  }

  return (
    <>
      {open && (
        <section
          className="chat-panel"
          role="dialog"
          aria-modal="false"
          aria-labelledby="chat-title"
          onKeyDown={(e) => {
            if (e.key === "Escape") close();
          }}
        >
          <div className="chat-heading">
            <span className="chat-symbol">↗</span>
            <div>
              <h2 id="chat-title">TrailSupply support</h2>
              <p>Demo chat · AI not connected</p>
            </div>
            <button
              className="icon-button"
              onClick={close}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>
          <div
            className="chat-messages"
            role="log"
            aria-label="Chat messages"
            aria-live="polite"
          >
            {messages.map((message) => (
              <div key={message.id} className={"message " + message.role}>
                {message.text}
              </div>
            ))}
            <div ref={bottom} />
          </div>
          <form className="chat-form" onSubmit={send}>
            <label className="sr-only" htmlFor="chat-message">
              Your message
            </label>
            <input
              id="chat-message"
              ref={input}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Ask about gear, shipping, returns…"
              maxLength={1000}
            />
            <button
              type="submit"
              disabled={!text.trim()}
              aria-label="Send message"
            >
              ↑
            </button>
          </form>
          <p className="chat-note">
            Fictional store. No real purchases or refunds.
          </p>
        </section>
      )}
      <button
        ref={launcher}
        className="chat-launcher"
        onClick={() => {
          if (open) close();
          else setOpen(true);
        }}
        aria-expanded={open}
        aria-label={open ? "Close support chat" : "Open support chat"}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M20 11.5a8 8 0 0 1-8 8H5l-4 3 1.7-6.2A8 8 0 1 1 20 11.5Z"
            stroke="currentColor"
            strokeWidth="1.6"
          />
        </svg>
        <span>Ask TrailSupply</span>
      </button>
    </>
  );
}
