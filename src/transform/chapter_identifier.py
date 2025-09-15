import instructor
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import ChapterInfo, ChaptersOnPage
from .page_iterator import iterate_pages_with_lines

load_dotenv()

class ChapterIdentifier:
    """LLM-based chapter identifier for EU regulations"""

    def __init__(self):
        """Initialize with OpenRouter client using GPT-5"""
        self.client = instructor.from_openai(
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        )
        self.model = "openai/gpt-5-mini"

    def identify_chapters_on_page(self, page_text: str, page_num: int) -> ChaptersOnPage:
        """
        Identify chapters on a single page using LLM.

        Args:
            page_text: Text with line numbers from single page
            page_num: Page number being processed

        Returns:
            ChaptersOnPage with all chapters found on this page
        """
        try:
            result = self.client.chat.completions.create(
                model=self.model,
                response_model=ChaptersOnPage,
                messages=[
                    {
                        "role": "system",
                        "content": """You are analyzing a single page of an EU regulation to identify CHAPTER headings.

Look for text patterns like:
- "CHAPTER I" followed by a title
- "CHAPTER II" followed by a title
- "CHAPTER III" followed by a title
- etc.

IMPORTANT:
- Only identify CHAPTER headings with Roman numerals (I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
- Ignore articles, sections, or other structures
- Return exact line numbers from the numbered text provided
- Extract the complete chapter title that follows the chapter number
- Each chapter should have both number and title"""
                    },
                    {
                        "role": "user",
                        "content": f"""Find any CHAPTER headings on this page (page {page_num}):

{page_text}

Identify:
- chapter_number: Roman numeral (I, II, III, etc.)
- title: Complete chapter title
- start_line: Exact line number where "CHAPTER" appears
- page_number: {page_num}
- confidence: Your confidence level (0-100)

Set has_chapters to true if any chapters found, false otherwise."""
                    }
                ]
            )
            return result

        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            print(f"API Key present: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
            return ChaptersOnPage(
                page_number=page_num,
                chapters=[],
                has_chapters=False
            )

    def extract_all_chapters(self, pdf_path: str, start_page: int = 1, end_page: int = None) -> List[ChapterInfo]:
        """
        Extract all chapters from PDF by iterating through pages sequentially.

        Args:
            pdf_path: Path to the PDF file
            start_page: Starting page number (default: 1)
            end_page: Ending page number (default: None for all pages)

        Returns:
            List of all ChapterInfo found across all pages
        """
        all_chapters = []
        pages_processed = 0

        print(f"Processing pages {start_page} to {end_page or 'end'} for chapters...")

        for page_num, page_text, line_offset in iterate_pages_with_lines(pdf_path):
            if page_num < start_page:
                continue
            if end_page and page_num > end_page:
                break

            print(f"  Checking page {page_num}...")

            chapters_on_page = self.identify_chapters_on_page(page_text, page_num)
            pages_processed += 1

            if chapters_on_page.has_chapters:
                print(f"    Found {len(chapters_on_page.chapters)} chapter(s)")
                for chapter in chapters_on_page.chapters:
                    print(f"      CHAPTER {chapter.chapter_number}: {chapter.title} (line {chapter.start_line})")

                all_chapters.extend(chapters_on_page.chapters)
            else:
                print(f"    No chapters found")

        print(f"\nTotal: Found {len(all_chapters)} chapters across {pages_processed} pages")
        return all_chapters

    def extract_all_chapters_parallel(self, pdf_path: str, start_page: int = 1, end_page: int = None, max_workers: int = 5) -> List[ChapterInfo]:
        """
        Extract all chapters from PDF using parallel processing.

        Args:
            pdf_path: Path to the PDF file
            start_page: Starting page number (default: 1)
            end_page: Ending page number (default: None for all pages)
            max_workers: Maximum number of parallel workers (default: 5)

        Returns:
            List of all ChapterInfo found across all pages
        """
        print(f"Processing pages {start_page} to {end_page or 'end'} for chapters (parallel with {max_workers} workers)...")

        # Collect all pages to process
        pages_to_process = []
        for page_num, page_text, line_offset in iterate_pages_with_lines(pdf_path):
            if page_num < start_page:
                continue
            if end_page and page_num > end_page:
                break
            pages_to_process.append((page_num, page_text))

        print(f"Found {len(pages_to_process)} pages to process")

        all_chapters = []

        # Process pages in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all pages for processing
            future_to_page = {
                executor.submit(self.identify_chapters_on_page, page_text, page_num): page_num
                for page_num, page_text in pages_to_process
            }

            # Collect results as they complete
            completed_pages = 0
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                completed_pages += 1

                try:
                    chapters_on_page = future.result()
                    print(f"  Page {page_num} completed ({completed_pages}/{len(pages_to_process)})")

                    if chapters_on_page.has_chapters:
                        print(f"    Found {len(chapters_on_page.chapters)} chapter(s)")
                        for chapter in chapters_on_page.chapters:
                            print(f"      CHAPTER {chapter.chapter_number}: {chapter.title} (line {chapter.start_line})")

                        all_chapters.extend(chapters_on_page.chapters)

                except Exception as e:
                    print(f"    Error processing page {page_num}: {e}")

        # Sort chapters by line number to maintain document order
        all_chapters.sort(key=lambda ch: ch.start_line)

        print(f"\nTotal: Found {len(all_chapters)} chapters across {len(pages_to_process)} pages")
        return all_chapters

    def extract_all_chapters_auto(self, pdf_path: str, max_workers: int = 4) -> List[ChapterInfo]:
        """
        Brute force extract all chapters from entire PDF document.
        Scans every page from start to end.

        Args:
            pdf_path: Path to the PDF file
            max_workers: Maximum number of parallel workers (default: 4)

        Returns:
            List of all ChapterInfo found in the document
        """
        print("Brute force scanning entire document for chapters...")

        # Get total pages by iterating through document
        total_pages = 0
        for page_num, _, _ in iterate_pages_with_lines(pdf_path):
            total_pages = page_num

        print(f"   Total pages in document: {total_pages}")
        print(f"   Scanning all pages from 1 to {total_pages}...")

        # Extract chapters from entire document
        chapters = self.extract_all_chapters_parallel(
            pdf_path,
            start_page=1,
            end_page=total_pages,
            max_workers=max_workers
        )

        if chapters:
            print(f"   Successfully found {len(chapters)} chapters")
        else:
            print(f"   No chapters found in this document")

        return chapters

    def validate_chapter_sequence(self, chapters: List[ChapterInfo]) -> dict:
        """
        Validate that chapters follow proper Roman numeral sequence.

        Args:
            chapters: List of ChapterInfo to validate

        Returns:
            Dictionary with validation results
        """
        roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
                         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]

        chapter_numbers = [ch.chapter_number for ch in chapters]

        # Check if sequence is valid
        expected_sequence = roman_numerals[:len(chapters)]
        is_sequential = chapter_numbers == expected_sequence

        return {
            "total_chapters": len(chapters),
            "chapter_numbers": chapter_numbers,
            "expected_sequence": expected_sequence,
            "is_sequential": is_sequential,
            "missing_chapters": [num for num in expected_sequence if num not in chapter_numbers],
            "unexpected_chapters": [num for num in chapter_numbers if num not in expected_sequence]
        }