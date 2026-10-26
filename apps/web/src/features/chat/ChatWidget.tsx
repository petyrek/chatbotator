import { useEffect, useRef, useState, type FormEvent } from "react";
import { MAX_CHAT_MESSAGES, sendChat, type ChatMessage } from "../../api";
import "./chat.css";

// A chat message plus a stable id for React's `key`.
type Message = ChatMessage & { id: string };

// Shown in the UI only. It is not part of the conversation sent to the API,
// which must start with a user message.
const GREETING =
  "Hi! I'm the TrailSupply assistant. Ask me about our gear, shipping, returns or warranty.";

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);
  useEffect(() => {
    if (open) bottom.current?.scrollIntoView({ block: "nearest" });
  }, [messages, pending, open]);

  // Each exchange adds two messages; stop before the API would reject the next one.
  const conversationFull = messages.length + 1 > MAX_CHAT_MESSAGES;

  function startNewConversation() {
    setMessages([]);
    setError(null);
    input.current?.focus();
  }

  function close() {
    setOpen(false);
    launcher.current?.focus();
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    const question = text.trim();
    if (!question || pending || conversationFull) return;

    const conversation: Message[] = [
      ...messages,
      { id: crypto.randomUUID(), role: "user", content: question },
    ];
    setMessages(conversation);
    setText("");
    setError(null);
    setPending(true);

    try {
      const reply = await sendChat(
        conversation.map(({ role, content }) => ({ role, content })),
      );
      setMessages([
        ...conversation,
        { id: crypto.randomUUID(), role: "assistant", content: reply },
      ]);
    } catch (err) {
      // Take the unanswered question out of the conversation and put it back
      // in the input, so trying again is one click (unless a new draft was typed
      // while waiting).
      setMessages(messages);
      setText((draft) => (draft.trim() ? draft : question));
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
      input.current?.focus();
    }
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
              <p>AI assistant · answers can be wrong</p>
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
            <div className="message assistant">{GREETING}</div>
            {messages.map((message) => (
              <div key={message.id} className={"message " + message.role}>
                {message.content}
              </div>
            ))}
            {pending && (
              <div className="message assistant pending">Thinking…</div>
            )}
            <div ref={bottom} />
          </div>
          {conversationFull && (
            <p className="chat-error">
              This conversation has reached its length limit.{" "}
              <button
                type="button"
                className="chat-link"
                onClick={startNewConversation}
              >
                Start a new conversation
              </button>
            </p>
          )}
          {error && (
            <p className="chat-error" role="alert">
              {error}
            </p>
          )}
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
              disabled={pending || conversationFull || !text.trim()}
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
