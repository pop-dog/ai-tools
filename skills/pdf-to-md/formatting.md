# Formatting Reference

This file contains prompt templates and formatting instructions used by the pdf-to-md skill.
Claude reads this file during conversion to guide LLM formatting steps.

---

## Book title extraction

**Task**: Extract the canonical book title from the first 1-3 pages of a PDF.

**Prompt template**:
```
Given the following text extracted from the first pages of a book, return only the canonical
book title. If you cannot determine the title with confidence, return the empty string.
Output nothing except the title itself — no explanation, no quotes.

Text:
{first_pages_text}
```

**Rules**:
- Return only the title, no author, subtitle, or edition unless part of the canonical title
- If uncertain, return empty string (caller will fall back to filename)

---

## Per-page markdown formatting

**Task**: Convert raw PDF-extracted text for a single page into clean markdown.

**Prompt template**:
```
Convert the following raw text extracted from page {page_num} of "{book_title}" into clean markdown.

Rules:
- Preserve all content faithfully — do not summarize or omit anything
- Format headings with appropriate # levels based on visual hierarchy
- Format lists as markdown bullet or numbered lists
- Format footnotes as markdown footnotes at the bottom of the page: [^1]: footnote text
- Bold and italic text should be preserved where clearly intentional
- Do not add any content not present in the source text
- If you identify this page as having multi-column layout, note it but do your best
- If the page content is ambiguous, malformed, or hard to parse, set needs_review to true

At the end of your response, on a new line, output a JSON object with this exact structure:
{{"needs_review": true/false, "reason": "brief reason if needs_review is true, else null"}}

Raw text:
{page_text}
```

---

## Table reconstruction (LLM fallback)

**Task**: Reconstruct a malformed table as a markdown table.

**Prompt template**:
```
The following text was extracted from a table in a PDF but the column alignment is broken.
Reconstruct it as a valid markdown table. Preserve all data exactly.
If you cannot confidently reconstruct the table, return the raw text unchanged.

Raw table text:
{table_text}
```

---

## Chapter detection (LLM fallback)

**Task**: Identify chapter boundaries when no TOC is available.

**Prompt template**:
```
The following are the first lines of each page from a PDF book, numbered by page.
Identify which pages start a new chapter. For each chapter start, return the page number
and the chapter title.

Output a JSON array of objects with this structure:
[{{"page": 1, "title": "Introduction"}}, ...]

Output nothing except the JSON array.

Pages:
{page_previews}
```
