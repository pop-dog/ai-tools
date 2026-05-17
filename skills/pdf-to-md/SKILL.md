---
name: pdf-to-md
description: Converts a PDF book into a structured tree of markdown files organized by chapter and page. Use when the user wants to convert a PDF to markdown, mentions "pdf-to-md", or says "activate pdf-to-md skill". Each output page file has YAML frontmatter with citation metadata (page, chapter, book).
---

# pdf-to-md

Converts a text-layer PDF into a folder tree of markdown files:

```
<book-slug>/
├── assets/                        # extracted images
├── 01-chapter-title/
│   ├── 0001.md
│   └── 0002.md
└── 02-next-chapter/
    └── 0003.md
```

Each page file contains YAML frontmatter and LLM-formatted markdown body.

## How to use this skill

1. Ask the user for the PDF path if not provided
2. Optionally ask for an output directory (default: current working directory)
3. Run `setup.sh` to install dependencies (idempotent, safe to run every time)
4. Read `formatting.md` for LLM prompt templates before starting
5. Run `scripts/convert.py` and respond to its LLM prompts as they appear
6. Report the output location when done

## Invocation

```bash
# Install dependencies (idempotent)
bash setup.sh

# Convert a PDF
python scripts/convert.py /path/to/book.pdf [output_dir]
```

## LLM interaction protocol

`convert.py` is an orchestration script that delegates LLM tasks back to you (Claude).
It communicates via stdout/stdin using delimited blocks:

- `---TITLE_EXTRACTION_INPUT_START---` / `---TITLE_EXTRACTION_INPUT_END---`: extract book title
- `---CHAPTER_DETECTION_INPUT_START---` / `---CHAPTER_DETECTION_INPUT_END---`: detect chapters
- `---PAGE_FORMAT_INPUT_START page=N---` / `---PAGE_FORMAT_INPUT_END---`: format a page
- `---TABLE_INPUT_START---` / `---TABLE_INPUT_END---`: reconstruct a malformed table

After each block, the script prints an instruction and waits for your input via `input()`.
Respond exactly as the prompt template in `formatting.md` specifies.

## Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` | Idempotent dependency installer. Run before anything else. Referenced here for debugging — if dependencies fail to install, inspect this script first. |
| `scripts/convert.py` | Main orchestration entry point. Calls `setup.sh`, coordinates extraction and LLM steps, writes output files. |
| `scripts/extract.py` | PDF extraction: text (with header/footer stripping), tables (pdfplumber), images (PyMuPDF), TOC, page metadata. |
| `scripts/output.py` | File and folder writing: creates directory structure, writes page markdown files with frontmatter, saves images to assets. |

## Reference files

| File | Purpose |
|------|---------|
| `formatting.md` | Prompt templates for all LLM steps: title extraction, chapter detection, page formatting, table reconstruction. Read this before processing. |

## Page frontmatter fields

```yaml
---
page: 42
chapter: 3
chapter_title: "Backpropagation"
book: deep-learning-goodfellow
title: "Deep Learning"
needs_review: false
---
```

`needs_review: true` is set when:
- Page has very little extractable content (figure-heavy or near-blank page)
- Table reconstruction fell back to LLM (uncertain quality)
- LLM flagged ambiguous or malformed content during formatting
- Page is the first or last page of a chapter (boundary pages are often partial)

## Resumability

If conversion is interrupted, re-running the same command resumes from where it stopped.
Existing page files are skipped automatically — no data is overwritten.

## V1 limitations and TODOs

- **Scanned PDFs**: Not supported. Pages with no extractable text raise an error with a clear message. TODO: add OCR support (requires rethinking header/footer, TOC, and geometry assumptions).
- **Multi-column layout**: Not reflowed. Columns may be interleaved in output. TODO: use bounding box clustering to detect and reorder columns correctly.
- **Parallelism**: Pages are processed sequentially. TODO: parallel chapter processing for large books.
