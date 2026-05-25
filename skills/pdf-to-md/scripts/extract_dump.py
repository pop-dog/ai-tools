#!/usr/bin/env python3
"""Dumps all PDF page data to JSON for offline LLM processing."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from extract import open_pdf, extract_first_pages_text, extract_toc, extract_page, ScannedPDFError

def main():
    pdf_path = sys.argv[1]
    fitz_doc, plumber_doc = open_pdf(pdf_path)
    total = len(fitz_doc)

    out = {
        "total_pages": total,
        "first_pages_text": extract_first_pages_text(fitz_doc),
        "toc": [{"chapter_num": e.chapter_num, "title": e.title, "start_page": e.start_page}
                for e in extract_toc(fitz_doc)],
        "pages": [],
    }

    for page_num in range(1, total + 1):
        try:
            p = extract_page(fitz_doc, plumber_doc, page_num)
            out["pages"].append({
                "page_num": page_num,
                "text": p.text,
                "tables": p.tables,
                "is_low_content": p.is_low_content,
                "table_used_llm_fallback": p.table_used_llm_fallback,
                "image_count": len(p.images),
            })
        except ScannedPDFError as e:
            out["pages"].append({"page_num": page_num, "error": str(e)})

    fitz_doc.close()
    plumber_doc.close()
    print(json.dumps(out))

if __name__ == "__main__":
    main()
