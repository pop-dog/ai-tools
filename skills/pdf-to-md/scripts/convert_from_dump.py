#!/usr/bin/env python3
"""
Converts a pdf-to-md JSON dump to markdown files using heuristic formatting.
Usage: python convert_from_dump.py <dump.json> <output_dir>
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import TocEntry, slugify
from output import (
    make_book_dir, make_chapter_dir, page_already_exists, write_page
)


def format_page_text(text: str) -> tuple[str, bool, str | None]:
    """
    Heuristic markdown formatter for PDF-extracted text.
    Returns (markdown_body, needs_review, reason).
    """
    lines = text.splitlines()
    out = []
    i = 0
    needs_review = False
    reason = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            out.append("")
            i += 1
            continue

        # Detect headings: short ALL-CAPS lines (likely section headers in RPG books)
        if (len(stripped) <= 60
                and stripped == stripped.upper()
                and re.search(r"[A-Z]", stripped)
                and not stripped.startswith("|")):
            # Determine heading level by length
            if len(stripped) <= 25:
                out.append(f"## {stripped.title()}")
            else:
                out.append(f"### {stripped.title()}")
            i += 1
            continue

        # Detect numbered list items
        if re.match(r"^\d+[\.\)]\s+\S", stripped):
            out.append(stripped)
            i += 1
            continue

        # Detect bullet-like lines (•, *, -, —)
        if re.match(r"^[•\-\*—]\s+\S", stripped):
            bullet_text = re.sub(r"^[•\-\*—]\s+", "- ", stripped)
            out.append(bullet_text)
            i += 1
            continue

        # Table rows (pipe-delimited, already formatted by extract step)
        if stripped.startswith("|"):
            out.append(stripped)
            i += 1
            continue

        # Bold-like: short lines followed by a blank or indented text (stat block labels)
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if (len(stripped) <= 40
                and stripped.endswith(":")
                and next_line and not next_line.startswith("|")):
            out.append(f"**{stripped}**")
            i += 1
            continue

        # Default: plain paragraph text
        out.append(stripped)
        i += 1

    # Collapse multiple blank lines
    result_lines = []
    prev_blank = False
    for line in out:
        if line == "":
            if not prev_blank:
                result_lines.append("")
            prev_blank = True
        else:
            result_lines.append(line)
            prev_blank = False

    return "\n".join(result_lines).strip(), needs_review, reason


def assign_chapters(toc: list[TocEntry], total_pages: int) -> dict[int, TocEntry]:
    mapping: dict[int, TocEntry] = {}
    for i, entry in enumerate(toc):
        end_page = toc[i + 1].start_page - 1 if i + 1 < len(toc) else total_pages
        for p in range(entry.start_page, end_page + 1):
            mapping[p] = entry
    if toc:
        for p in range(1, toc[0].start_page):
            mapping[p] = toc[0]
    return mapping


def is_chapter_boundary(page_num: int, chapter_mapping: dict[int, TocEntry]) -> bool:
    if page_num not in chapter_mapping:
        return False
    entry = chapter_mapping[page_num]
    pages_in_chapter = [p for p, e in chapter_mapping.items() if e is entry]
    return page_num == min(pages_in_chapter) or page_num == max(pages_in_chapter)


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_from_dump.py <dump.json> <output_dir>")
        sys.exit(1)

    dump_path = sys.argv[1]
    output_dir = sys.argv[2]

    data = json.loads(Path(dump_path).read_text())
    total_pages = data["total_pages"]
    book_title = "The Delian Tomb"
    book_slug = slugify(book_title)

    toc = [TocEntry(chapter_num=e["chapter_num"], title=e["title"], start_page=e["start_page"])
           for e in data["toc"]]

    chapter_mapping = assign_chapters(toc, total_pages)
    book_dir = make_book_dir(output_dir, book_slug)
    chapter_dirs = {e.chapter_num: make_chapter_dir(book_dir, e.chapter_num, slugify(e.title))
                    for e in toc}

    pages_by_num = {p["page_num"]: p for p in data["pages"]}

    errors = []
    for page_num in range(1, total_pages + 1):
        chapter_entry = chapter_mapping.get(page_num, toc[0])
        chapter_dir = chapter_dirs[chapter_entry.chapter_num]

        if page_already_exists(chapter_dir, page_num):
            print(f"[{page_num}/{total_pages}] Skipping (exists).")
            continue

        page = pages_by_num.get(page_num)
        if not page:
            print(f"[{page_num}/{total_pages}] No data, skipping.")
            continue

        if "error" in page:
            print(f"[{page_num}/{total_pages}] Scanned/error page — writing stub.")
            write_page(
                chapter_dir=chapter_dir,
                page_num=page_num,
                chapter_num=chapter_entry.chapter_num,
                chapter_title=chapter_entry.title,
                book_slug=book_slug,
                book_title=book_title,
                needs_review=True,
                markdown_body="*(No extractable text — likely a full-page image or scanned page.)*",
                image_refs=[],
            )
            continue

        # Format the page text
        raw_text = page["text"]
        if page.get("tables"):
            table_blocks = []
            for t in page["tables"]:
                rows = t["rows"]
                if rows:
                    header = "| " + " | ".join(str(c) for c in rows[0]) + " |"
                    sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
                    body = "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows[1:])
                    table_blocks.append("\n".join([header, sep, body]))
            if table_blocks:
                raw_text += "\n\n" + "\n\n".join(table_blocks)

        markdown_body, llm_needs_review, review_reason = format_page_text(raw_text)

        boundary = is_chapter_boundary(page_num, chapter_mapping)
        needs_review = (
            page.get("is_low_content", False)
            or page.get("table_used_llm_fallback", False)
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
            image_refs=[],
        )
        print(f"[{page_num}/{total_pages}] Done. needs_review={needs_review}")

    print(f"\nDone. Output: {book_dir}")
    if errors:
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
