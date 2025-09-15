import instructor
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import ArticleInfo, ArticlesOnPage, ChapterInfo
from .page_iterator import iterate_pages_with_lines
import re

load_dotenv()

class ArticleIdentifier:
    """LLM-based article identifier for EU regulations"""

    def __init__(self):
        """Initialize with OpenRouter client using GPT-5"""
        self.client = instructor.from_openai(
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        )
        self.model = "openai/gpt-5-mini"

    def identify_articles_on_page(self, page_text: str, page_num: int, current_chapter: Optional[str] = None) -> ArticlesOnPage:
        """
        Identify articles on a single page using LLM.

        Args:
            page_text: Text with line numbers from single page
            page_num: Page number being processed
            current_chapter: Current chapter context (e.g., "I", "II")

        Returns:
            ArticlesOnPage with all articles found on this page
        """
        try:
            result = self.client.chat.completions.create(
                model=self.model,
                response_model=ArticlesOnPage,
                messages=[
                    {
                        "role": "system",
                        "content": """You are analyzing a single page of an EU regulation to identify ARTICLE headings.

Look for text patterns like:
- "Article 1" followed by a title
- "Article 2" followed by a title
- "Article 3" followed by a title
- etc.

IMPORTANT:
- Only identify ARTICLE headings with numbers (1, 2, 3, 4, etc.)
- Ignore references to other articles in the text content
- Return exact line numbers from the numbered text provided
- Extract the complete article title that follows the article number
- Each article should have both number and title
- Articles belong to the current chapter context"""
                    },
                    {
                        "role": "user",
                        "content": f"""Find any ARTICLE headings on this page (page {page_num}):

Current chapter context: {current_chapter or 'Unknown'}

{page_text}

Identify:
- article_number: Integer (1, 2, 3, etc.)
- title: Complete article title
- start_line: Exact global line number where "Article" appears
- parent_chapter: "{current_chapter or 'Unknown'}"
- start_page: {page_num}
- confidence: Your confidence level (0-100)

Set has_articles to true if any articles found, false otherwise."""
                    }
                ]
            )
            return result

        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            print(f"API Key present: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
            return ArticlesOnPage(
                page_number=page_num,
                articles=[],
                has_articles=False
            )

    def extract_all_articles_with_chapters(self, pdf_path: str, chapters: List[ChapterInfo]) -> List[ArticleInfo]:
        """
        Extract all articles from PDF within chapter boundaries (sequential processing).

        Args:
            pdf_path: Path to the PDF file
            chapters: List of chapters to provide context

        Returns:
            List of all ArticleInfo found across all pages
        """
        all_articles = []

        print(f"Extracting articles within {len(chapters)} chapters...")

        # Sort chapters by start line to process in order
        sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

        # Process each chapter's content for articles
        for i, chapter in enumerate(sorted_chapters):
            next_chapter_line = sorted_chapters[i + 1].start_line if i + 1 < len(sorted_chapters) else None

            print(f"  Processing Chapter {chapter.chapter_number}: {chapter.title}")

            # Extract articles within this chapter
            chapter_articles = self._extract_articles_in_chapter(
                pdf_path,
                chapter,
                next_chapter_line
            )

            # Set chapter boundaries for articles
            for article in chapter_articles:
                article.parent_chapter = chapter.chapter_number

            all_articles.extend(chapter_articles)
            print(f"    Found {len(chapter_articles)} articles in Chapter {chapter.chapter_number}")

        # Set article boundaries (end_line for each article)
        self._set_article_boundaries(all_articles)

        print(f"\nTotal: Found {len(all_articles)} articles across {len(chapters)} chapters")
        return all_articles

    def extract_all_articles_with_chapters_parallel(self, pdf_path: str, chapters: List[ChapterInfo], max_workers: int = 4) -> List[ArticleInfo]:
        """
        Extract all articles from PDF within chapter boundaries (parallel processing).

        Args:
            pdf_path: Path to the PDF file
            chapters: List of chapters to provide context
            max_workers: Maximum number of parallel workers

        Returns:
            List of all ArticleInfo found across all pages
        """
        all_articles = []

        print(f"Extracting articles within {len(chapters)} chapters (parallel with {max_workers} workers)...")

        # Sort chapters by start line to process in order
        sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

        # Collect all pages that might contain articles for all chapters
        all_relevant_pages = []
        chapter_page_mapping = {}

        for i, chapter in enumerate(sorted_chapters):
            next_chapter_line = sorted_chapters[i + 1].start_line if i + 1 < len(sorted_chapters) else None

            # Find relevant pages for this chapter
            chapter_pages = []
            for page_num, page_text, line_offset in iterate_pages_with_lines(pdf_path):
                page_lines = page_text.strip().split('\n')

                # Check if this page contains content within chapter boundaries
                page_start_line = line_offset + 1
                page_end_line = line_offset + len(page_lines)

                # Skip pages before chapter starts
                if page_end_line < chapter.start_line:
                    continue

                # Skip pages after next chapter starts
                if next_chapter_line and page_start_line > next_chapter_line:
                    break

                # This page may contain chapter content
                page_data = (page_num, page_text, line_offset, chapter.chapter_number)
                chapter_pages.append(page_data)
                all_relevant_pages.append(page_data)

            chapter_page_mapping[chapter.chapter_number] = len(chapter_pages)

        print(f"Found {len(all_relevant_pages)} pages to process across all chapters")

        # Process pages in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all pages for processing
            future_to_page = {
                executor.submit(self.identify_articles_on_page, page_text, page_num, chapter_number): (page_num, chapter_number)
                for page_num, page_text, line_offset, chapter_number in all_relevant_pages
            }

            # Collect results as they complete
            completed_pages = 0
            for future in as_completed(future_to_page):
                page_num, chapter_number = future_to_page[future]
                completed_pages += 1

                try:
                    articles_on_page = future.result()
                    print(f"  Page {page_num} (Chapter {chapter_number}) completed ({completed_pages}/{len(all_relevant_pages)})")

                    if articles_on_page.has_articles:
                        print(f"    Found {len(articles_on_page.articles)} article(s)")
                        for article in articles_on_page.articles:
                            print(f"      Article {article.article_number}: {article.title} (line {article.start_line})")

                        # Filter articles to ensure they're within correct chapter boundaries
                        for article in articles_on_page.articles:
                            # Find the chapter this article belongs to
                            for chapter in sorted_chapters:
                                if chapter.chapter_number == chapter_number:
                                    next_chapter = next((ch for ch in sorted_chapters if ch.start_line > chapter.start_line), None)
                                    next_chapter_line = next_chapter.start_line if next_chapter else None

                                    # Check if article is within chapter boundaries
                                    if article.start_line >= chapter.start_line:
                                        if next_chapter_line is None or article.start_line < next_chapter_line:
                                            article.parent_chapter = chapter_number
                                            all_articles.append(article)
                                    break

                except Exception as e:
                    print(f"    Error processing page {page_num}: {e}")

        # Sort articles by start line to maintain document order
        all_articles.sort(key=lambda art: art.start_line)

        # Set article boundaries (end_line for each article)
        self._set_article_boundaries(all_articles)

        # Show summary by chapter
        articles_by_chapter = {}
        for article in all_articles:
            chapter = article.parent_chapter
            if chapter not in articles_by_chapter:
                articles_by_chapter[chapter] = []
            articles_by_chapter[chapter].append(article)

        for chapter, articles in articles_by_chapter.items():
            print(f"  Chapter {chapter}: Found {len(articles)} articles")

        print(f"\nTotal: Found {len(all_articles)} articles across {len(chapters)} chapters")
        return all_articles

    def extract_all_articles_with_chapters_auto(self, pdf_path: str, chapters: List[ChapterInfo], max_workers: int = 4) -> List[ArticleInfo]:
        """
        Auto extract all articles from PDF with optimal performance.
        Uses parallel processing for faster extraction.

        Args:
            pdf_path: Path to the PDF file
            chapters: List of chapters to provide context
            max_workers: Maximum number of parallel workers (default: 4)

        Returns:
            List of all ArticleInfo found across all chapters
        """
        print("Auto-extracting articles with parallel processing...")

        # Use parallel extraction for better performance
        articles = self.extract_all_articles_with_chapters_parallel(
            pdf_path,
            chapters,
            max_workers=max_workers
        )

        if articles:
            print(f"   Successfully found {len(articles)} articles")

            # Validate article sequences
            validation = self.validate_article_sequence(articles)
            for chapter, chapter_validation in validation.items():
                if not chapter_validation['is_sequential']:
                    print(f"   Warning: Chapter {chapter} has non-sequential articles: {chapter_validation['article_numbers']}")
                else:
                    print(f"   Chapter {chapter}: Sequential articles {chapter_validation['article_numbers'][0]}-{chapter_validation['article_numbers'][-1]}")
        else:
            print(f"   No articles found in this document")

        return articles

    def _extract_articles_in_chapter(self, pdf_path: str, chapter: ChapterInfo, next_chapter_line: Optional[int]) -> List[ArticleInfo]:
        """
        Extract articles within a specific chapter's boundaries.

        Args:
            pdf_path: Path to PDF file
            chapter: Chapter to extract articles from
            next_chapter_line: Line where next chapter starts (or None if last chapter)

        Returns:
            List of articles found in this chapter
        """
        chapter_articles = []

        # Collect pages that might contain this chapter's articles
        relevant_pages = []

        for page_num, page_text, line_offset in iterate_pages_with_lines(pdf_path):
            page_lines = page_text.strip().split('\n')

            # Check if this page contains content within chapter boundaries
            page_start_line = line_offset + 1
            page_end_line = line_offset + len(page_lines)

            # Skip pages before chapter starts
            if page_end_line < chapter.start_line:
                continue

            # Skip pages after next chapter starts
            if next_chapter_line and page_start_line > next_chapter_line:
                break

            # This page may contain chapter content
            relevant_pages.append((page_num, page_text, line_offset))

        # Process relevant pages for articles
        for page_num, page_text, line_offset in relevant_pages:
            articles_on_page = self.identify_articles_on_page(
                page_text,
                page_num,
                chapter.chapter_number
            )

            if articles_on_page.has_articles:
                # Filter articles to only those within chapter boundaries
                for article in articles_on_page.articles:
                    # Check if article is actually within this chapter
                    if article.start_line >= chapter.start_line:
                        if next_chapter_line is None or article.start_line < next_chapter_line:
                            chapter_articles.append(article)

        return chapter_articles

    def _set_article_boundaries(self, articles: List[ArticleInfo]) -> None:
        """
        Set end_line for each article based on where the next article starts.

        Args:
            articles: List of articles to set boundaries for (modified in place)
        """
        # Sort articles by start line
        sorted_articles = sorted(articles, key=lambda art: art.start_line)

        for i, article in enumerate(sorted_articles):
            if i + 1 < len(sorted_articles):
                # Article ends where next article starts
                next_article = sorted_articles[i + 1]
                article.end_line = next_article.start_line - 1
            else:
                # Last article - we'll need to determine its end differently
                # For now, leave it as None - can be handled during content extraction
                article.end_line = None

    def extract_article_content(self, pdf_path: str, article: ArticleInfo) -> str:
        """
        Extract full content of an article using its line boundaries.

        Args:
            pdf_path: Path to PDF file
            article: Article info with start_line and end_line

        Returns:
            Full text content of the article
        """
        content_lines = []

        for page_num, page_text, line_offset in iterate_pages_with_lines(pdf_path):
            page_lines = page_text.strip().split('\n')

            for line_idx, line in enumerate(page_lines):
                current_line_num = line_offset + line_idx + 1

                # Check if this line is within article boundaries
                if current_line_num >= article.start_line:
                    if article.end_line is None or current_line_num <= article.end_line:
                        # Extract the actual content (remove line number prefix)
                        parts = line.split(':', 1)
                        if len(parts) > 1 and parts[0].strip().isdigit():
                            content_lines.append(parts[1].strip())
                        else:
                            content_lines.append(line.strip())
                    else:
                        # We've reached the end of this article
                        break

        return '\n'.join(content_lines)

    def validate_article_sequence(self, articles: List[ArticleInfo]) -> dict:
        """
        Validate that articles follow proper sequential numbering within chapters.

        Args:
            articles: List of ArticleInfo to validate

        Returns:
            Dictionary with validation results
        """
        # Group articles by chapter
        articles_by_chapter = {}
        for article in articles:
            chapter = article.parent_chapter
            if chapter not in articles_by_chapter:
                articles_by_chapter[chapter] = []
            articles_by_chapter[chapter].append(article)

        validation_results = {}

        for chapter, chapter_articles in articles_by_chapter.items():
            # Sort by article number
            sorted_articles = sorted(chapter_articles, key=lambda art: art.article_number)
            article_numbers = [art.article_number for art in sorted_articles]

            # Check if sequence is valid (1, 2, 3, ...)
            expected_sequence = list(range(1, len(article_numbers) + 1))
            is_sequential = article_numbers == expected_sequence

            validation_results[chapter] = {
                "total_articles": len(chapter_articles),
                "article_numbers": article_numbers,
                "expected_sequence": expected_sequence,
                "is_sequential": is_sequential,
                "missing_articles": [num for num in expected_sequence if num not in article_numbers],
                "unexpected_articles": [num for num in article_numbers if num not in expected_sequence]
            }

        return validation_results