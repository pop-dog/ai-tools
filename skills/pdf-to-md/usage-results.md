# Usage Results

## Bash tool incompatibility with convert.py

`convert.py` uses `input()` to receive LLM responses via stdin after printing each
`---*_START---` / `---*_END---` delimiter block. The Bash tool runs commands
non-interactively and cannot write to a running process's stdin, so `convert.py`
cannot be used directly.

### Workaround (used for *The Pragmatic Programmer*, 352 pages)

Two additional scripts were written to replace the interactive flow:

- **`scripts/extract_all.py`** — One-shot extraction pass. Opens the PDF, extracts
  text/tables/images/TOC/page previews for every page, and serializes everything to
  a JSON file. Run once before any LLM work.

- **`scripts/write_all.py`** — Reads the extracted JSON and writes all markdown
  output files using rule-based formatting (all-caps lines → `##` headings, TIP
  lines → blockquotes, etc.) and a manually specified chapter structure. Skips
  already-written pages, so it is resumable.

## Page numbering mismatch (TODO)

The `page` frontmatter field currently reflects the PDF's physical page index
(1-based from the first page of the file). This does not match the book's printed
page numbers:

- Front matter pages (praise, title, TOC, foreword, preface) are either unnumbered
  or use roman numerals (i, ii, … xxiv).
- The book's arabic page 1 corresponds to PDF page 26 (Chapter 1: A Pragmatic
  Philosophy).

As a result, a reader looking up "page 34" in the book will not find it at
`0034.md` — they would need to add the front-matter offset (25 pages in this
edition).

**TODO:** Add a `pdf_page` field (physical PDF index) alongside the existing
`page` field, and populate `page` with the printed page number extracted from
the page text (or left null for unnumbered front-matter pages). The roman-numeral
pages could use a `page_roman` field or simply be stored as strings.

---

### Suggested fix for the skill

Replace the stdin/stdout protocol in `convert.py` with a file-based handoff:
write each LLM input block to a temp file, have Claude read and respond via a
second file, then have the script poll for the response file. This would work
with the Bash tool without requiring a separate extraction script.
