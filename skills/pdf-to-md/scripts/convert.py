#!/usr/bin/env python3
"""
pdf-to-md converter — main entry point.

Usage:
    python convert.py <pdf_path> [output_dir]

Converts a text-layer PDF into a folder tree of markdown files:
    <output_dir>/<book-slug>/<NN-chapter-title>/<NNNN>.md

Each page file has YAML frontmatter with citation metadata.
Requires Claude (this script is invoked by the pdf-to-md skill; Claude performs LLM steps).

V1 limitations:
    - Text-layer PDFs only (scanned PDFs raise ScannedPDFError)
    - Sequential processing (parallelism is a TODO)
    - Multi-column layout is not reflowed (TODO)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Run setup before importing dependencies
subprocess.run(
    ["bash", str(Path(__file__).parent.parent / "setup.sh")],
    check=True,
)

from extract import (  # noqa: E402
    ScannedPDFError,
    TocEntry,
    extract_first_pages_text,
    extract_page,
    extract_toc,
    open_pdf,
    slugify,
)
from output import (  # noqa: E402
    make_book_dir,
    make_chapter_dir,
    page_already_exists,
    write_image,
    write_page,
)


# ---------------------------------------------------------------------------
# LLM helpers — these functions print a structured request and read a response
# from Claude, which is orchestrating this script.
# ---------------------------------------------------------------------------

def llm_extract_title(first_pages_text: str) -> str:
    """
    Asks Claude to extract the book title from the first pages.
    Claude reads formatting.md for the prompt template.
    Returns a slugified title, or empty string if uncertain.
    """
    print("\n[LLM] Extracting book title from first pages...")
    print("---TITLE_EXTRACTION_INPUT_START---")
    print(first_pages_text[:3000])
    print("---TITLE_EXTRACTION_INPUT_END---")
    print(
        "Please extract the book title from the text above, following the template in "
        "formatting.md. Reply with ONLY the title on a single line, or an empty line if uncertain."
    )
    title = input().strip()
    return title


def llm_detect_chapters(page_previews: list[tuple[int, str]]) -> list[TocEntry]:
    """
    Asks Claude to detect chapter boundaries when no TOC is available.
    page_previews: list of (page_num, first_line) tuples.
    Returns list of TocEntry.
    """
    print("\n[LLM] No TOC found. Detecting chapter boundaries...")
    preview_text = "\n".join(f"Page {p}: {line}" for p, line in page_previews)
    print("---CHAPTER_DETECTION_INPUT_START---")
    print(preview_text)
    print("---CHAPTER_DETECTION_INPUT_END---")
    print(
        "Please identify chapter boundaries following the template in formatting.md. "
        "Reply with ONLY a JSON array."
    )
    raw = input().strip()
    try:
        entries = json.loads(raw)
        return [
            TocEntry(chapter_num=i + 1, title=e["title"], start_page=e["page"])
            for i, e in enumerate(entries)
        ]
    except (json.JSONDecodeError, KeyError):
        print("[WARN] Could not parse chapter detection response. Treating entire book as one chapter.")
        return [TocEntry(chapter_num=1, title="Book", start_page=1)]


def llm_format_page(page_num: int, book_title: str, page_text: str) -> tuple[str, bool, str | None]:
    """
    Asks Claude to format page text as markdown.
    Returns (markdown_body, needs_review, reason).
    Claude reads formatting.md for the prompt template.
    """
    print(f"\n[LLM] Formatting page {page_num}...")
    print(f"---PAGE_FORMAT_INPUT_START page={page_num}---")
    print(page_text)
    print("---PAGE_FORMAT_INPUT_END---")
    print(
        f"Please format the above text as markdown for page {page_num} of '{book_title}', "
        "following the template in formatting.md. End your response with the JSON object "
        "as specified."
    )
    lines = []
    while True:
        line = input()
        lines.append(line)
        if line.startswith("{") and line.endswith("}"):
            break

    # Split markdown body from trailing JSON
    json_line = lines[-1]
    markdown_body = "\n".join(lines[:-1]).strip()

    try:
        meta = json.loads(json_line)
        needs_review = bool(meta.get("needs_review", False))
        reason = meta.get("reason")
    except json.JSONDecodeError:
        markdown_body = "\n".join(lines).strip()
        needs_review = True
        reason = "Could not parse LLM metadata response"

    return markdown_body, needs_review, reason


def llm_reconstruct_table(table_rows: list[list[str]]) -> str:
    """
    Asks Claude to reconstruct a malformed table as a markdown table.
    Returns markdown table string.
    """
    raw_text = "\n".join("\t".join(row) for row in table_rows)
    print("\n[LLM] Reconstructing malformed table...")
    print("---TABLE_INPUT_START---")
    print(raw_text)
    print("---TABLE_INPUT_END---")
    print(
        "Please reconstruct the above as a markdown table following the template in "
        "formatting.md. Reply with ONLY the markdown table."
    )
    lines = []
    while True:
        line = input()
        if not line and lines and lines[-1].startswith("|"):
            break
        lines.append(line)
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Chapter mapping
# ---------------------------------------------------------------------------

def assign_chapters(toc: list[TocEntry], total_pages: int) -> dict[int, TocEntry]:
    """
    Returns a mapping of page_num -> TocEntry for every page in the book.
    Pages before the first chapter entry are assigned to chapter 1.
    """
    mapping: dict[int, TocEntry] = {}
    for i, entry in enumerate(toc):
        end_page = toc[i + 1].start_page - 1 if i + 1 < len(toc) else total_pages
        for p in range(entry.start_page, end_page + 1):
            mapping[p] = entry
    # Pages before first chapter (e.g. front matter)
    if toc:
        for p in range(1, toc[0].start_page):
            mapping[p] = toc[0]
    return mapping


def is_chapter_boundary(page_num: int, chapter_mapping: dict[int, TocEntry]) -> bool:
    """Returns True if page is the first or last page of its chapter."""
    if page_num not in chapter_mapping:
        return False
    entry = chapter_mapping[page_num]
    pages_in_chapter = [p for p, e in chapter_mapping.items() if e is entry]
    return page_num == min(pages_in_chapter) or page_num == max(pages_in_chapter)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert.py <pdf_path> [output_dir]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()

    if not Path(pdf_path).exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    print(f"[pdf-to-md] Opening {pdf_path}...")
    fitz_doc, plumber_doc = open_pdf(pdf_path)
    total_pages = len(fitz_doc)
    print(f"[pdf-to-md] {total_pages} pages detected.")

    # --- Book title ---
    first_pages_text = extract_first_pages_text(fitz_doc)
    raw_title = llm_extract_title(first_pages_text)
    if raw_title:
        book_title = raw_title
        book_slug = slugify(raw_title)
    else:
        book_title = Path(pdf_path).stem
        book_slug = slugify(book_title)
    print(f"[pdf-to-md] Book: '{book_title}' → folder: '{book_slug}'")

    # --- Chapter structure ---
    toc = extract_toc(fitz_doc)
    if toc:
        print(f"[pdf-to-md] TOC found: {len(toc)} chapters.")
    else:
        print("[pdf-to-md] No TOC found, using LLM chapter detection...")
        previews = []
        for i in range(min(total_pages, 500)):
            page = fitz_doc[i]
            first_line = page.get_text("text").strip().splitlines()[0] if page.get_text("text").strip() else ""
            previews.append((i + 1, first_line))
        toc = llm_detect_chapters(previews)

    chapter_mapping = assign_chapters(toc, total_pages)

    # --- Output dirs ---
    book_dir = make_book_dir(output_dir, book_slug)
    chapter_dirs: dict[int, Path] = {}
    for entry in toc:
        chapter_dirs[entry.chapter_num] = make_chapter_dir(
            book_dir, entry.chapter_num, slugify(entry.title)
        )

    # --- Per-page processing ---
    errors = []
    for page_num in range(1, total_pages + 1):
        chapter_entry = chapter_mapping.get(page_num, toc[0])
        chapter_dir = chapter_dirs[chapter_entry.chapter_num]

        if page_already_exists(chapter_dir, page_num):
            print(f"[{page_num}/{total_pages}] Skipping page {page_num} (already exists).")
            continue

        print(f"[{page_num}/{total_pages}] Processing page {page_num}...")

        try:
            page_data = extract_page(fitz_doc, plumber_doc, page_num)
        except ScannedPDFError as e:
            print(f"[ERROR] {e}")
            errors.append((page_num, str(e)))
            continue

        # Reconstruct malformed tables via LLM
        table_markdown_blocks = []
        for table in page_data.tables:
            if table["needs_llm"]:
                md_table = llm_reconstruct_table(table["rows"])
            else:
                # Format well-formed table as markdown
                rows = table["rows"]
                header = "| " + " | ".join(rows[0]) + " |"
                separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
                body = "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
                md_table = "\n".join([header, separator, body])
            table_markdown_blocks.append(md_table)

        # Combine text and tables for LLM formatting
        page_text_with_tables = page_data.text
        if table_markdown_blocks:
            page_text_with_tables += "\n\n" + "\n\n".join(table_markdown_blocks)

        # LLM markdown formatting
        markdown_body, llm_needs_review, _ = llm_format_page(
            page_num, book_title, page_text_with_tables
        )

        # Save images
        image_refs = []
        for img in page_data.images:
            ref = write_image(book_dir, page_num, img["index"], img["ext"], img["data"])
            image_refs.append(ref)

        # Determine needs_review
        boundary = is_chapter_boundary(page_num, chapter_mapping)
        needs_review = (
            page_data.is_low_content
            or page_data.table_used_llm_fallback
            or llm_needs_review
            or boundary
        )

        write_page(
            chapter_dir=chapter_dir,
            page_num=page_num,
            chapter_num=chapter_entry.chapter_num,
            chapter_title=chapter_entry.title,
            book_slug=book_slug,
            book_title=book_title,
            needs_review=needs_review,
            markdown_body=markdown_body,
            image_refs=image_refs,
        )

    fitz_doc.close()
    plumber_doc.close()

    print(f"\n[pdf-to-md] Done. Output: {book_dir}")
    if errors:
        print(f"[pdf-to-md] {len(errors)} page(s) failed:")
        for page_num, msg in errors:
            print(f"  Page {page_num}: {msg}")


if __name__ == "__main__":
    main()
