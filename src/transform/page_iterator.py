import pdfplumber
from typing import Generator, Tuple

def iterate_pages_with_lines(pdf_path: str) -> Generator[Tuple[int, str, int], None, None]:
    """
    Iterate through PDF pages and yield text with line numbers.

    Args:
        pdf_path: Path to the PDF file

    Yields:
        tuple: (page_number, page_text_with_lines, global_line_offset)
            - page_number: 1-indexed page number
            - page_text_with_lines: Text with line numbers prefixed
            - global_line_offset: Starting line number for this page
    """
    global_line_number = 1

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()

            if page_text:
                # Split into lines and add line numbers
                page_lines = page_text.split('\n')
                numbered_lines = []

                for line in page_lines:
                    if line.strip():  # Only add non-empty lines
                        numbered_lines.append(f"{global_line_number:4d}: {line}")
                        global_line_number += 1

                if numbered_lines:  # Only yield if page has content
                    page_with_lines = '\n'.join(numbered_lines)
                    yield page_num, page_with_lines, global_line_number - len(numbered_lines)

def get_page_range(pdf_path: str, start_page: int = 1, end_page: int = None) -> Generator[Tuple[int, str, int], None, None]:
    """
    Get a specific range of pages from PDF.

    Args:
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-indexed)
        end_page: Ending page number (1-indexed), None for all pages

    Yields:
        tuple: (page_number, page_text_with_lines, global_line_offset)
    """
    for page_num, page_text, line_offset in iterate_pages_with_lines(pdf_path):
        if page_num >= start_page:
            if end_page is None or page_num <= end_page:
                yield page_num, page_text, line_offset
            else:
                break