"""
File and folder writing for pdf-to-md output.
Handles the book/chapter/page directory structure and asset storage.
"""

from pathlib import Path


def make_book_dir(output_dir: str | Path, book_slug: str) -> Path:
    book_dir = Path(output_dir) / book_slug
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / "assets").mkdir(exist_ok=True)
    return book_dir


def make_chapter_dir(book_dir: Path, chapter_num: int, chapter_slug: str) -> Path:
    folder_name = f"{chapter_num:02d}-{chapter_slug}"
    chapter_dir = book_dir / folder_name
    chapter_dir.mkdir(parents=True, exist_ok=True)
    return chapter_dir


def page_file_path(chapter_dir: Path, page_num: int) -> Path:
    return chapter_dir / f"{page_num:04d}.md"


def page_already_exists(chapter_dir: Path, page_num: int) -> bool:
    return page_file_path(chapter_dir, page_num).exists()


def write_page(
    chapter_dir: Path,
    page_num: int,
    chapter_num: int,
    chapter_title: str,
    book_slug: str,
    book_title: str,
    needs_review: bool,
    markdown_body: str,
    image_refs: list[str],
) -> Path:
    """Writes a single page markdown file with YAML frontmatter."""
    path = page_file_path(chapter_dir, page_num)

    frontmatter_lines = [
        "---",
        f"page: {page_num}",
        f"chapter: {chapter_num}",
        f'chapter_title: "{chapter_title}"',
        f"book: {book_slug}",
        f'title: "{book_title}"',
        f"needs_review: {str(needs_review).lower()}",
        "---",
        "",
    ]

    image_section = ""
    if image_refs:
        image_section = "\n\n" + "\n".join(image_refs)

    content = "\n".join(frontmatter_lines) + markdown_body + image_section + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def write_image(book_dir: Path, page_num: int, img_index: int, ext: str, data: bytes) -> str:
    """
    Saves an image to the global assets folder.
    Returns the relative markdown image reference string.
    """
    filename = f"page_{page_num:04d}_img_{img_index}.{ext}"
    asset_path = book_dir / "assets" / filename
    asset_path.write_bytes(data)

    # Relative path from chapter dir (one level deep) back to assets
    return f"![](../assets/{filename})"
