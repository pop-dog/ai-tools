#!/usr/bin/env python3
"""
One-shot extraction: dumps all page data from a PDF to a JSON file.
Used by the orchestrator to separate extraction from LLM formatting.
"""

import json
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import (
    open_pdf, extract_toc, extract_first_pages_text,
    extract_page, ScannedPDFError, slugify, TocEntry
)


def main():
    if len(sys.argv) < 3:
        print("Usage: extract_all.py <pdf_path> <output_json>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_json = sys.argv[2]

    print(f"Opening {pdf_path}...")
    fitz_doc, plumber_doc = open_pdf(pdf_path)
    total_pages = len(fitz_doc)
    print(f"{total_pages} pages detected.")

    first_pages_text = extract_first_pages_text(fitz_doc)

    toc = extract_toc(fitz_doc)
    toc_data = [{"chapter_num": e.chapter_num, "title": e.title, "start_page": e.start_page} for e in toc]

    # First-line previews for chapter detection
    previews = []
    for i in range(total_pages):
        page = fitz_doc[i]
        text = page.get_text("text").strip()
        first_line = text.splitlines()[0] if text else ""
        previews.append({"page": i + 1, "first_line": first_line})

    # Extract all pages
    pages = []
    errors = []
    for page_num in range(1, total_pages + 1):
        if page_num % 20 == 0:
            print(f"  Extracting page {page_num}/{total_pages}...")
        try:
            pd = extract_page(fitz_doc, plumber_doc, page_num)
            # Encode image data as base64 for JSON serialization
            images_out = []
            for img in pd.images:
                images_out.append({
                    "page_num": img["page_num"],
                    "index": img["index"],
                    "ext": img["ext"],
                    "data_b64": base64.b64encode(img["data"]).decode("ascii"),
                })
            pages.append({
                "page_num": page_num,
                "text": pd.text,
                "tables": pd.tables,
                "images": images_out,
                "is_low_content": pd.is_low_content,
                "table_used_llm_fallback": pd.table_used_llm_fallback,
            })
        except ScannedPDFError as e:
            print(f"  [ERROR] Page {page_num}: {e}")
            errors.append({"page_num": page_num, "error": str(e)})
            pages.append({
                "page_num": page_num,
                "text": "",
                "tables": [],
                "images": [],
                "is_low_content": True,
                "table_used_llm_fallback": False,
                "error": str(e),
            })

    fitz_doc.close()
    plumber_doc.close()

    data = {
        "total_pages": total_pages,
        "first_pages_text": first_pages_text,
        "toc": toc_data,
        "previews": previews,
        "pages": pages,
        "errors": errors,
    }

    print(f"Writing to {output_json}...")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Done. {len(pages)} pages extracted, {len(errors)} errors.")


if __name__ == "__main__":
    main()
