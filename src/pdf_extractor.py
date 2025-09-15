import pdfplumber
from typing import Tuple, List, Dict

def extract_text(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        str: Extracted text from all pages
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_with_line_numbers(pdf_path: str) -> Tuple[str, Dict[int, Tuple[int, int]]]:
    """
    Extract text from PDF with line numbers and page mapping.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        tuple: (numbered_text, line_to_page_mapping)
            - numbered_text: Text with line numbers prefixed
            - line_to_page_mapping: Dict mapping line numbers to (page_num, line_in_page)
    """
    numbered_lines = []
    line_to_page = {}
    current_line = 1

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if page_text:
                page_lines = page_text.split('\n')
                for line_in_page, line in enumerate(page_lines, 1):
                    if line.strip():  # Skip completely empty lines
                        numbered_lines.append(f"{current_line:4d}: {line}")
                        line_to_page[current_line] = (page_num, line_in_page)
                        current_line += 1

    return "\n".join(numbered_lines), line_to_page

def extract_lines_range(pdf_path: str, start_line: int, end_line: int) -> str:
    """
    Extract specific line range from PDF.

    Args:
        pdf_path: Path to the PDF file
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed)

    Returns:
        str: Extracted text from the specified line range
    """
    numbered_text, _ = extract_text_with_line_numbers(pdf_path)
    lines = numbered_text.split('\n')

    # Filter lines within the range
    extracted_lines = []
    for line in lines:
        if line.strip():
            line_num = int(line.split(':')[0].strip())
            if start_line <= line_num <= end_line:
                # Remove line number prefix for clean output
                text_part = ':'.join(line.split(':')[1:]).strip()
                extracted_lines.append(text_part)

    return '\n'.join(extracted_lines)