"""Turns the citations in a model response into the policy lines they point to."""

from dataclasses import dataclass

from anthropic.types import Message

from chatbotator.policies import Document


@dataclass(frozen=True)
class Citation:
    document: str  # file name, e.g. "returns.md"
    title: str  # e.g. "Returns & refunds"
    section: str  # e.g. "Return window"
    quote: str  # the cited text as sent, with its section: "Return window: ..."


def citations_in(response: Message, documents: list[Document]) -> list[Citation]:
    """The policy lines a response cites, in order, each listed once.

    Each citation says which search result (= document) and which content block
    (= passage) it cites, so we can look up the passage's section. A citation can
    span several passages (start_block_index to end_block_index); we take the
    section of the first. Citations only give positions, so `documents` must be
    the list that was sent, in the same order.
    """
    citations: list[Citation] = []
    for block in response.content:
        if block.type != "text":
            continue
        # None when a block cites nothing (like `?? []` in TS).
        for cited in block.citations or []:
            if cited.type != "search_result_location":
                continue
            document = documents[cited.search_result_index]
            passage = document.passages[cited.start_block_index]
            citation = Citation(
                document.name, document.title, passage.section, cited.cited_text
            )
            if citation not in citations:  # the same line is often cited twice
                citations.append(citation)
    return citations
