# Journal

After each session, record one design decision and one lesson (see PLAN.md, Working rules).

## 2026-10-26 — Setup

- **Decision:** Backend in Python/FastAPI instead of Node, so the AI and evaluation work happens in the language most AI engineering tooling and roles assume. The web app stays React/TypeScript.
- **Lesson:**

## 2026-10-27 — Grounded answers

- **Decision:** Send all four policy documents with every question instead of retrieving passages. Measured first: keyword retrieval (BM25, top 4) found only 7 of the 14 passages the dev cases need. Its misses were vocabulary gaps ("send something back" vs "return"), product names outranking policy sections, and answers spanning two sections. The whole knowledge base is about 3,300 input tokens per request, so sending everything costs about $0.0003 per question and can't miss anything. Retrieval becomes worth it when the documents stop fitting.
- **Decision:** Citations use the API's `search_result` blocks, one text block per policy bullet, so each citation quotes the exact line.
- **Result:** With documents, the dev set went from 1/10 to 10/10 passing (behaviour 10/10, required points 27/27, forbidden claims 0/12).
- **Lesson:** An open-ended "find unsupported claims" judge was noisy (it flagged text that is in the policy almost word for word). Splitting the reply into statements, requiring a supporting quote for each, and checking in code that the quote exists made it reliable. Its remaining flags were real: a reply called the backpack "the bottle", and the policies never say how to request a return. Graders also need everything the bot had, including what the customer said.
