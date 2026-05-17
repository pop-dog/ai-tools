"""
PDF extraction utilities: text, tables, images, TOC, and metadata.
Uses PyMuPDF for text/images/layout and pdfplumber for table detection.
V1 supports text-layer PDFs only — scanned PDFs will raise ScannedPDFError.
"""

import re
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from dataclasses import dataclass, field


class ScannedPDFError(Exception):
    pass


@dataclass
class PageData:
    page_num: int        # 1-based
    text: str
    tables: list[list[list[str]]]   # list of tables; each table is rows of cells
    images: list[dict]               # {"bbox": (x,y,w,h), "data": bytes, "ext": str}
    is_low_content: bool = False
    table_used_llm_fallback: bool = False


@dataclass
class TocEntry:
    chapter_num: int
    title: str
    start_page: int      # 1-based


# Header/footer exclusion: top and bottom 5% of page height
HEADER_FOOTER_MARGIN = 0.05


def _is_scanned_page(page: fitz.Page) -> bool:
    """Returns True if the page has no extractable text (likely scanned)."""
    return not page.get_text("text").strip()


def open_pdf(pdf_path: str) -> tuple[fitz.Document, pdfplumber.PDF]:
    fitz_doc = fitz.open(pdf_path)
    plumber_doc = pdfplumber.open(pdf_path)
    return fitz_doc, plumber_doc


def extract_toc(fitz_doc: fitz.Document) -> list[TocEntry]:
    """
    Extracts TOC from PDF metadata. Returns empty list if no TOC is found.
    fitz TOC entries: [level, title, page_num (1-based)]
    """
    raw = fitz_doc.get_toc(simple=True)
    if not raw:
        return []

    # Filter to top-level entries only (level == 1) as chapter boundaries
    chapters = [entry for entry in raw if entry[0] == 1]
    result = []
    for i, (_, title, page) in enumerate(chapters):
        result.append(TocEntry(
            chapter_num=i + 1,
            title=title.strip(),
            start_page=page,
        ))
    return result


def extract_first_pages_text(fitz_doc: fitz.Document, n: int = 3) -> str:
    """Returns concatenated text from the first n pages for title extraction."""
    parts = []
    for i in range(min(n, len(fitz_doc))):
        parts.append(fitz_doc[i].get_text("text"))
    return "\n".join(parts)


def _content_bbox(page: fitz.Page) -> fitz.Rect:
    """Returns a rect excluding top and bottom header/footer margins."""
    r = page.rect
    margin = r.height * HEADER_FOOTER_MARGIN
    return fitz.Rect(r.x0, r.y0 + margin, r.x1, r.y1 - margin)


def _extract_text(fitz_page: fitz.Page) -> str:
    """Extracts text within the content bounding box (strips header/footer)."""
    clip = _content_bbox(fitz_page)
    return fitz_page.get_text("text", clip=clip).strip()


def _is_table_well_formed(table: list[list[str | None]]) -> bool:
    """Heuristic: a table is well-formed if all rows have the same column count."""
    if not table:
        return False
    col_counts = {len(row) for row in table}
    return len(col_counts) == 1 and list(col_counts)[0] > 1


def _extract_tables(plumber_page: pdfplumber.page.Page) -> tuple[list, bool]:
    """
    Extracts tables using pdfplumber.
    Returns (tables, used_llm_fallback_flag).
    Malformed tables are marked for LLM fallback (handled by convert.py).
    """
    raw_tables = plumber_page.extract_tables()
    if not raw_tables:
        return [], False

    tables = []
    used_fallback = False
    for raw in raw_tables:
        # Normalise None cells to empty string
        table = [[cell or "" for cell in row] for row in raw]
        if _is_table_well_formed(table):
            tables.append({"rows": table, "needs_llm": False})
        else:
            tables.append({"rows": table, "needs_llm": True})
            used_fallback = True

    return tables, used_fallback


def _extract_images(fitz_page: fitz.Page, page_num: int) -> list[dict]:
    """Extracts embedded images from a page."""
    images = []
    doc = fitz_page.parent
    clip = _content_bbox(fitz_page)

    for img_index, img in enumerate(fitz_page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        if not base_image:
            continue

        # Check image bbox is within content area (skip header/footer images)
        rects = fitz_page.get_image_rects(xref)
        if rects and not any(clip.intersects(r) for r in rects):
            continue

        images.append({
            "page_num": page_num,
            "index": img_index + 1,
            "data": base_image["image"],
            "ext": base_image["ext"],
        })

    return images


def extract_page(
    fitz_doc: fitz.Document,
    plumber_doc: pdfplumber.PDF,
    page_num: int,  # 1-based
) -> PageData:
    """Extracts all content from a single page."""
    fitz_page = fitz_doc[page_num - 1]
    plumber_page = plumber_doc.pages[page_num - 1]

    if _is_scanned_page(fitz_page):
        raise ScannedPDFError(
            f"Page {page_num} has no extractable text. "
            "This PDF appears to be scanned. OCR support is not yet implemented."
        )

    text = _extract_text(fitz_page)
    tables, used_llm_fallback = _extract_tables(plumber_page)
    images = _extract_images(fitz_page, page_num)

    is_low_content = len(text.strip()) < 100 and not tables and not images

    return PageData(
        page_num=page_num,
        text=text,
        tables=tables,
        images=images,
        is_low_content=is_low_content,
        table_used_llm_fallback=used_llm_fallback,
    )


def slugify(text: str) -> str:
    """Converts text to a lowercase hyphenated slug with no spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")
