"""Tests for parsing the policy Markdown into documents and passages."""

from chatbotator.policies import DOCUMENTS, Passage, parse_document

POLICY = """\
# Returns & refunds

Last updated: 26 October 2026. Not a statement of legal rights.

## Return window

- The delivery date counts as day 0.
- Day 31 or later is too late.

## Condition

- Items must be unused.
"""


def test_keeps_the_title_and_each_bullet_under_its_heading() -> None:
    document = parse_document("returns.md", POLICY)

    assert document.name == "returns.md"
    assert document.title == "Returns & refunds"
    assert document.passages == [
        Passage("Return window", "The delivery date counts as day 0."),
        Passage("Return window", "Day 31 or later is too late."),
        Passage("Condition", "Items must be unused."),
    ]  # the "Last updated" intro line is not a passage


def test_loads_the_store_documents_in_a_stable_order() -> None:
    names = [document.name for document in DOCUMENTS]

    assert names == ["faq.md", "returns.md", "shipping.md", "warranty.md"]
