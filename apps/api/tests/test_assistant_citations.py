"""Tests for citations_in: turning the API's citations into policy lines."""

from anthropic.types import CitationsSearchResultLocation, Message, TextBlock

from chatbotator.assistant.citations import Citation, citations_in
from chatbotator.policies import Document, Passage

RETURNS = Document(
    "returns.md",
    "Returns & refunds",
    [Passage("Return window", "Day 0 is delivery."), Passage("Condition", "Unused.")],
)


def cites(start: int, end: int, text: str) -> CitationsSearchResultLocation:
    """A citation as the API returns it: passages start..end (end exclusive) of
    the first document sent."""
    # model_construct() builds the SDK object without validation.
    return CitationsSearchResultLocation.model_construct(
        type="search_result_location",
        cited_text=text,
        search_result_index=0,
        start_block_index=start,
        end_block_index=end,
    )


def response(*blocks: TextBlock) -> Message:
    return Message.model_construct(content=list(blocks))


def test_looks_up_the_section_and_lists_each_line_once() -> None:
    line = cites(0, 1, "Return window: Day 0 is delivery.")
    reply = response(
        TextBlock.model_construct(type="text", text="Day 0.", citations=[line]),
        TextBlock.model_construct(type="text", text=" So:", citations=None),
        TextBlock.model_construct(type="text", text=" day 0.", citations=[line]),
    )

    assert citations_in(reply, [RETURNS]) == [
        Citation(
            "returns.md",
            "Returns & refunds",
            "Return window",
            "Return window: Day 0 is delivery.",
        )
    ]


def test_a_citation_spanning_passages_takes_the_first_section() -> None:
    both = cites(0, 2, "Return window: Day 0 is delivery. Condition: Unused.")
    reply = response(TextBlock.model_construct(type="text", text="…", citations=[both]))

    [citation] = citations_in(reply, [RETURNS])

    assert citation.section == "Return window"
