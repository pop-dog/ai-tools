#!/usr/bin/env python3
"""
Direct orchestrator: reads extracted JSON data and writes all markdown files.
Uses smart rule-based formatting for headings, code, and lists, plus LLM
formatting for complex pages if desired.
"""

import json
import re
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from output import (
    make_book_dir, make_chapter_dir, page_already_exists, write_image, write_page
)
from extract import slugify, TocEntry


# ---------------------------------------------------------------------------
# Chapter structure (manually detected from TOC and page previews)
# ---------------------------------------------------------------------------

CHAPTERS = [
    TocEntry(chapter_num=1,  title="Front Matter",                 start_page=1),
    TocEntry(chapter_num=2,  title="A Pragmatic Philosophy",       start_page=26),
    TocEntry(chapter_num=3,  title="A Pragmatic Approach",         start_page=50),
    TocEntry(chapter_num=4,  title="The Basic Tools",              start_page=96),
    TocEntry(chapter_num=5,  title="Pragmatic Paranoia",           start_page=132),
    TocEntry(chapter_num=6,  title="Bend, or Break",               start_page=162),
    TocEntry(chapter_num=7,  title="While You Are Coding",         start_page=196),
    TocEntry(chapter_num=8,  title="Before the Project",           start_page=226),
    TocEntry(chapter_num=9,  title="Pragmatic Projects",           start_page=248),
    TocEntry(chapter_num=10, title="Appendix A - Resources",       start_page=286),
    TocEntry(chapter_num=11, title="Appendix B - Answers",         start_page=304),
    TocEntry(chapter_num=12, title="Index",                        start_page=334),
]

BOOK_TITLE = "The Pragmatic Programmer"
BOOK_SLUG = "the-pragmatic-programmer"


# ---------------------------------------------------------------------------
# Rule-based markdown formatter
# ---------------------------------------------------------------------------

def is_all_caps_heading(line: str) -> bool:
    """Detect section headings: all-caps, at least 4 chars, may contain spaces."""
    stripped = line.strip()
    if len(stripped) < 4:
        return False
    # Allow letters, spaces, apostrophes, hyphens, commas
    cleaned = re.sub(r"[^A-Za-z]", "", stripped)
    if not cleaned:
        return False
    # Must be mostly uppercase
    upper_ratio = sum(1 for c in cleaned if c.isupper()) / len(cleaned)
    return upper_ratio > 0.9 and len(stripped) >= 4


def looks_like_code(line: str) -> bool:
    """Heuristic: lines starting with 4+ spaces or a tab are code."""
    return line.startswith("    ") or line.startswith("\t")


def format_table(table: dict) -> str:
    """Format a table dict (with 'rows' list) as markdown table."""
    rows = table.get("rows", [])
    if not rows:
        return ""
    header = "| " + " | ".join(str(c) for c in rows[0]) + " |"
    separator = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body_rows = [
        "| " + " | ".join(str(c) for c in row) + " |"
        for row in rows[1:]
    ]
    return "\n".join([header, separator] + body_rows)


def format_page_text(raw_text: str, tables: list) -> tuple[str, bool]:
    """
    Convert raw extracted text to markdown.
    Returns (markdown, needs_review).
    """
    if not raw_text.strip():
        # Table-only or image-only page
        table_md = "\n\n".join(format_table(t) for t in tables if t.get("rows"))
        return table_md or "", True

    lines = raw_text.splitlines()
    output_lines = []
    in_code_block = False
    needs_review = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Blank line
        if not line.strip():
            if in_code_block:
                output_lines.append("```")
                in_code_block = False
            output_lines.append("")
            i += 1
            continue

        # Code block detection
        if looks_like_code(line):
            if not in_code_block:
                output_lines.append("```")
                in_code_block = True
            output_lines.append(line.rstrip())
            i += 1
            continue
        else:
            if in_code_block:
                output_lines.append("```")
                in_code_block = False

        stripped = line.strip()

        # Page-number lines: single number or roman numeral — skip
        if re.match(r"^[xivXIV\d]+$", stripped) and len(stripped) <= 6:
            i += 1
            continue

        # All-caps section headings → ## heading
        if is_all_caps_heading(stripped):
            output_lines.append(f"\n## {stripped.title()}\n")
            i += 1
            continue

        # "Chapter N" or "Appendix X" opener → # heading
        if re.match(r"^(Chapter \d+|Appendix [A-Z])$", stripped):
            output_lines.append(f"# {stripped}")
            i += 1
            continue

        # TIP N lines → bold
        if re.match(r"^TIP \d+$", stripped):
            tip_num = stripped.split()[1]
            # Consume the next non-empty line as tip text
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                tip_text = lines[i].strip()
                output_lines.append(f"\n> **Tip {tip_num}:** {tip_text}\n")
                i += 1
            continue

        # Bullet-like lines starting with • or -
        if stripped.startswith("•"):
            output_lines.append("- " + stripped[1:].strip())
            i += 1
            continue

        # Footnote-like: starts with a number followed by period/dot
        if re.match(r"^\d+\.", stripped) and len(stripped) < 80:
            # Could be a numbered list item
            output_lines.append(stripped)
            i += 1
            continue

        output_lines.append(stripped)
        i += 1

    if in_code_block:
        output_lines.append("```")

    # Append table markdown if any
    if tables:
        table_sections = []
        for t in tables:
            tmd = format_table(t)
            if tmd:
                table_sections.append(tmd)
        if table_sections:
            output_lines.append("")
            output_lines.extend(table_sections)

    # Collapse 3+ consecutive blank lines to 2
    result_lines = []
    blank_count = 0
    for line in output_lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result_lines.append(line)
        else:
            blank_count = 0
            result_lines.append(line)

    return "\n".join(result_lines).strip(), needs_review


# ---------------------------------------------------------------------------
# Chapter assignment
# ---------------------------------------------------------------------------

def assign_chapters(chapters: list[TocEntry], total_pages: int) -> dict[int, TocEntry]:
    mapping = {}
    for i, entry in enumerate(chapters):
        end = chapters[i + 1].start_page - 1 if i + 1 < len(chapters) else total_pages
        for p in range(entry.start_page, end + 1):
            mapping[p] = entry
    return mapping


def is_boundary(page_num: int, mapping: dict[int, TocEntry]) -> bool:
    if page_num not in mapping:
        return False
    entry = mapping[page_num]
    pages = [p for p, e in mapping.items() if e is entry]
    return page_num == min(pages) or page_num == max(pages)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: write_all.py <extracted_json> [output_dir]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else str(Path.cwd())

    print(f"Loading {json_path}...")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    total_pages = data["total_pages"]
    print(f"Writing {total_pages} pages for '{BOOK_TITLE}'...")

    chapter_mapping = assign_chapters(CHAPTERS, total_pages)

    # Build output dirs
    book_dir = make_book_dir(output_dir, BOOK_SLUG)
    chapter_dirs = {}
    for entry in CHAPTERS:
        chapter_dirs[entry.chapter_num] = make_chapter_dir(
            book_dir, entry.chapter_num, slugify(entry.title)
        )

    skipped = 0
    written = 0
    errors = []

    for page_num in range(1, total_pages + 1):
        chapter_entry = chapter_mapping.get(page_num, CHAPTERS[0])
        chapter_dir = chapter_dirs[chapter_entry.chapter_num]

        if page_already_exists(chapter_dir, page_num):
            skipped += 1
            if page_num % 50 == 0:
                print(f"  [{page_num}/{total_pages}] Skipping already-done pages...")
            continue

        page_data = data["pages"][page_num - 1]

        # Save images
        image_refs = []
        for img in page_data.get("images", []):
            try:
                img_bytes = base64.b64decode(img["data_b64"])
                ref = write_image(book_dir, page_num, img["index"], img["ext"], img_bytes)
                image_refs.append(ref)
            except Exception as e:
                print(f"  [WARN] Page {page_num} image error: {e}")

        # Format page
        try:
            markdown_body, fmt_needs_review = format_page_text(
                page_data["text"], page_data.get("tables", [])
            )
        except Exception as e:
            markdown_body = page_data["text"]
            fmt_needs_review = True
            errors.append((page_num, str(e)))

        boundary = is_boundary(page_num, chapter_mapping)
        needs_review = (
            page_data.get("is_low_content", False)
            or page_data.get("table_used_llm_fallback", False)
            or fmt_needs_review
            or boundary
        )

        write_page(
            chapter_dir=chapter_dir,
            page_num=page_num,
            chapter_num=chapter_entry.chapter_num,
            chapter_title=chapter_entry.title,
            book_slug=BOOK_SLUG,
            book_title=BOOK_TITLE,
            needs_review=needs_review,
            markdown_body=markdown_body,
            image_refs=image_refs,
        )
        written += 1

        if page_num % 50 == 0:
            print(f"  [{page_num}/{total_pages}] Written {written} pages...")

    print(f"\nDone. Written: {written}, Skipped: {skipped}, Errors: {len(errors)}")
    print(f"Output: {book_dir}")
    if errors:
        print(f"Formatting errors:")
        for pg, msg in errors:
            print(f"  Page {pg}: {msg}")


if __name__ == "__main__":
    main()
