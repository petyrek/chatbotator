"""The store's policy documents: loads data/knowledge/*.md into titles and
passages. assistant/reply.py sends them all with every question.

All four come to about 3,000 input tokens as sent, so there is no retrieval
step: the model always sees everything. (We measured keyword retrieval first; it
found only 7 of 14 needed passages on our eval questions. See docs/journal.md.)
"""

from dataclasses import dataclass
from pathlib import Path

from chatbotator.settings import DATA_DIR

KNOWLEDGE_DIR = DATA_DIR / "knowledge"


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
    """Parses one policy file into its title and bullet passages.

    Keeps the title, then every bullet under a `## ` heading. The intro line
    ("Last updated ...") is not policy, so it is left out.
    """
    lines = markdown.splitlines()
    title = lines[0].removeprefix("# ").strip()
    passages: list[Passage] = []
    section: str | None = None  # the heading the next bullets belong to
    for line in lines[1:]:
        if line.startswith("## "):
            section = line.removeprefix("## ").strip()
        elif line.startswith("- ") and section:
            passages.append(
                Passage(section=section, text=line.removeprefix("- ").strip())
            )
    return Document(name=name, title=title, passages=passages)


def load_documents(directory: Path = KNOWLEDGE_DIR) -> list[Document]:
    """Every *.md in the folder, sorted by name. Citations point at documents by
    position, so the order must be the same every time."""
    return [
        parse_document(p.name, p.read_text()) for p in sorted(directory.glob("*.md"))
    ]


# Runs once, on first import (like a top-level const in an ES module): the
# documents don't change while the app runs.
DOCUMENTS = load_documents()
