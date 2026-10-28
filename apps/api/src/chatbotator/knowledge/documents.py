"""The store's policy documents, sent in full with every question.

The whole knowledge base is about 1,000 tokens, so there is no retrieval step:
the model always sees everything. (We measured keyword retrieval first; it found
only 7 of 14 needed passages on our eval questions. See docs/journal.md.)
"""

from dataclasses import dataclass
from pathlib import Path

from anthropic.types import SearchResultBlockParam

# documents.py -> knowledge -> chatbotator -> src -> api -> apps -> repo root
KNOWLEDGE_DIR = Path(__file__).resolve().parents[5] / "data" / "knowledge"


@dataclass(frozen=True)
class Passage:
    section: str  # the `##` heading it sits under, e.g. "Return window"
    text: str  # one bullet point: the smallest unit a citation can point to


@dataclass(frozen=True)
class Document:
    name: str  # file name, e.g. "returns.md"; sent as the citation source
    title: str  # e.g. "Returns & refunds"
    passages: list[Passage]


def parse_document(name: str, markdown: str) -> Document:
    """Keeps the title, then every bullet under a `## ` heading. The intro line
    ("Last updated ...") is not policy, so it is left out."""
    lines = markdown.splitlines()
    title = lines[0].removeprefix("# ").strip()
    passages, section = [], None
    for line in lines[1:]:
        if line.startswith("## "):
            section = line.removeprefix("## ").strip()
        elif line.startswith("- ") and section:
            passages.append(
                Passage(section=section, text=line.removeprefix("- ").strip())
            )
    return Document(name=name, title=title, passages=passages)


def load_documents(directory: Path = KNOWLEDGE_DIR) -> list[Document]:
    return [
        parse_document(p.name, p.read_text()) for p in sorted(directory.glob("*.md"))
    ]


# Loaded once when the app starts: the documents don't change while it runs.
DOCUMENTS = load_documents()


def as_search_results(documents: list[Document]) -> list[SearchResultBlockParam]:
    """The documents in the API's `search_result` format, with citations enabled.

    One text block per passage, so a citation quotes the exact policy line rather
    than the whole document. Each block starts with its section heading, so the
    model reads it in context.
    """
    return [
        {
            "type": "search_result",
            "source": document.name,
            "title": document.title,
            "content": [
                {"type": "text", "text": f"{p.section}: {p.text}"}
                for p in document.passages
            ],
            "citations": {"enabled": True},
        }
        for document in documents
    ]
