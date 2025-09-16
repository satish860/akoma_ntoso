import instructor
from openai import OpenAI
import os
import re
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import ArticleInfo, ArticleContent, ParagraphContent, SubparagraphContent, PointContent
from .page_iterator import iterate_pages_with_lines

load_dotenv()

class ArticleContentExtractor:
    """Extract article content using regex-first approach with LLM fallback"""

    def __init__(self, use_llm_fallback: bool = True):
        """
        Initialize extractor with regex patterns and optional LLM fallback.

        Args:
            use_llm_fallback: Whether to use LLM when regex parsing fails
        """
        self.use_llm_fallback = use_llm_fallback

        # Regex patterns for structure detection
        self.PARAGRAPH_PATTERN = re.compile(r'^(\d{1,2})\.\s+(.*)$')
        self.SUBPARA_PATTERN = re.compile(r'^\(([a-z])\)\s+(.*)$')
        self.POINT_PATTERN = re.compile(r'^\((i{1,3}|iv|v|vi{0,3}|ix|x|xi{0,3}|xiv|xv)\)\s+(.*)$')
        self.SUBPOINT_PATTERN = re.compile(r'^\(([a-z]{2})\)\s+(.*)$')  # (aa), (bb), (cc)

        # Initialize LLM client if fallback is enabled
        if self.use_llm_fallback:
            self.client = instructor.from_openai(
                OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                )
            )
            self.model = "openai/gpt-5-mini"

    def extract_all_articles_content_parallel(
        self,
        pdf_path: str,
        articles: List[ArticleInfo],
        max_workers: int = 8
    ) -> Dict[int, ArticleContent]:
        """
        Extract content for all articles in parallel using regex-first approach.

        Args:
            pdf_path: Path to PDF file
            articles: List of articles to extract content for
            max_workers: Number of parallel workers

        Returns:
            Dictionary mapping article_number to ArticleContent
        """
        print(f"Extracting content for {len(articles)} articles (regex-first, {max_workers} workers)...")

        article_contents = {}

        # Process articles in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all articles for processing
            future_to_article = {
                executor.submit(self.extract_single_article_content, pdf_path, article): article
                for article in articles
            }

            # Collect results as they complete
            completed_articles = 0
            regex_count = 0
            llm_count = 0
            failed_count = 0

            for future in as_completed(future_to_article):
                article = future_to_article[future]
                completed_articles += 1

                try:
                    content = future.result()
                    article_contents[article.article_number] = content

                    # Track extraction methods
                    if content.extraction_method == "regex":
                        regex_count += 1
                    elif content.extraction_method == "llm":
                        llm_count += 1
                    else:
                        failed_count += 1

                    print(f"  Article {article.article_number} completed ({completed_articles}/{len(articles)}) - {content.extraction_method}")

                except Exception as e:
                    print(f"  Error processing Article {article.article_number}: {e}")
                    failed_count += 1

                    # Create empty content as fallback
                    article_contents[article.article_number] = ArticleContent(
                        article_number=article.article_number,
                        title=article.title,
                        paragraphs=[],
                        extraction_method="failed"
                    )

        print(f"\nExtraction summary:")
        print(f"  Regex success: {regex_count} articles")
        print(f"  LLM fallback: {llm_count} articles")
        print(f"  Failed: {failed_count} articles")

        return article_contents

    def extract_single_article_content(self, pdf_path: str, article: ArticleInfo) -> ArticleContent:
        """
        Extract content for a single article with regex-first approach.

        Args:
            pdf_path: Path to PDF file
            article: Article to extract content for

        Returns:
            ArticleContent with structured content
        """
        # Step 1: Extract raw content using line boundaries
        raw_content = self.extract_raw_content(pdf_path, article)

        if not raw_content.strip():
            return ArticleContent(
                article_number=article.article_number,
                title=article.title,
                paragraphs=[],
                extraction_method="failed",
                raw_content=raw_content
            )

        # Step 2: Try regex parsing first
        try:
            paragraphs = self.parse_content_with_regex(raw_content, article.article_number)

            # Check if regex parsing was successful
            if paragraphs and len(paragraphs) > 0:
                return ArticleContent(
                    article_number=article.article_number,
                    title=article.title,
                    paragraphs=paragraphs,
                    extraction_method="regex",
                    raw_content=raw_content
                )
        except Exception as e:
            print(f"  Regex parsing failed for Article {article.article_number}: {e}")

        # Step 3: Fallback to LLM if regex failed and fallback is enabled
        if self.use_llm_fallback:
            try:
                return self.extract_article_content_llm(raw_content, article)
            except Exception as e:
                print(f"  LLM fallback failed for Article {article.article_number}: {e}")

        # Step 4: Return empty structure if all methods failed
        return ArticleContent(
            article_number=article.article_number,
            title=article.title,
            paragraphs=[],
            extraction_method="failed",
            raw_content=raw_content
        )

    def extract_raw_content(self, pdf_path: str, article: ArticleInfo) -> str:
        """
        Extract raw text content for an article using its line boundaries.

        Args:
            pdf_path: Path to PDF file
            article: Article with start_line and end_line

        Returns:
            Raw text content of the article
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

    def parse_content_with_regex(self, raw_content: str, article_number: int) -> List[ParagraphContent]:
        """
        Parse article content using regex patterns.

        Args:
            raw_content: Raw text content
            article_number: Article number for validation

        Returns:
            List of structured paragraphs
        """
        lines = [line.strip() for line in raw_content.split('\n') if line.strip()]
        paragraphs = []

        current_paragraph = None
        current_subparagraph = None
        current_point = None

        for line in lines:
            # Skip article header lines
            if (line.startswith(f'Article {article_number}') or
                line == str(article_number) or
                line == article_number):
                continue

            # Try paragraph pattern (1., 2., 3., etc.)
            para_match = self.PARAGRAPH_PATTERN.match(line)
            if para_match:
                # Save previous structures
                self._save_current_structures(current_point, current_subparagraph, current_paragraph, paragraphs)

                # Start new paragraph
                current_paragraph = ParagraphContent(
                    num=para_match.group(1),
                    content=[para_match.group(2)] if para_match.group(2) else [],
                    subparagraphs=[]
                )
                current_subparagraph = None
                current_point = None
                continue

            # Try subparagraph pattern ((a), (b), (c), etc.)
            subpara_match = self.SUBPARA_PATTERN.match(line)
            if subpara_match and current_paragraph:
                # Save previous point if exists
                if current_point and current_subparagraph:
                    current_subparagraph.points.append(current_point)
                # Save previous subparagraph if exists
                if current_subparagraph:
                    current_paragraph.subparagraphs.append(current_subparagraph)

                # Start new subparagraph
                current_subparagraph = SubparagraphContent(
                    marker=f"({subpara_match.group(1)})",
                    content=[subpara_match.group(2)] if subpara_match.group(2) else [],
                    points=[]
                )
                current_point = None
                continue

            # Try point pattern ((i), (ii), (iii), etc.)
            point_match = self.POINT_PATTERN.match(line)
            if point_match and current_subparagraph:
                # Save previous point if exists
                if current_point:
                    current_subparagraph.points.append(current_point)

                # Start new point
                current_point = PointContent(
                    marker=f"({point_match.group(1)})",
                    content=[point_match.group(2)] if point_match.group(2) else []
                )
                continue

            # Regular content line - add to current context
            if current_point:
                current_point.content.append(line)
            elif current_subparagraph:
                current_subparagraph.content.append(line)
            elif current_paragraph:
                current_paragraph.content.append(line)
            else:
                # Content before first paragraph - create implicit paragraph
                current_paragraph = ParagraphContent(
                    num="1",
                    content=[line],
                    subparagraphs=[]
                )

        # Save final structures
        self._save_current_structures(current_point, current_subparagraph, current_paragraph, paragraphs)

        return paragraphs

    def _save_current_structures(self, point, subparagraph, paragraph, paragraphs):
        """Helper method to save current parsing structures"""
        if point and subparagraph:
            subparagraph.points.append(point)
        if subparagraph and paragraph:
            paragraph.subparagraphs.append(subparagraph)
        if paragraph:
            paragraphs.append(paragraph)

    def extract_article_content_llm(self, raw_content: str, article: ArticleInfo) -> ArticleContent:
        """
        Fallback method using LLM to extract article content.
        Only called when regex parsing fails.

        Args:
            raw_content: Raw text content
            article: Article information

        Returns:
            ArticleContent extracted using LLM
        """
        try:
            result = self.client.chat.completions.create(
                model=self.model,
                response_model=ArticleContent,
                messages=[
                    {
                        "role": "system",
                        "content": """You are parsing the content of a legal article into structured format.

Identify:
- Paragraphs: numbered sections (1., 2., 3., etc.)
- Subparagraphs: lettered sections ((a), (b), (c), etc.)
- Points: roman numeral sections ((i), (ii), (iii), etc.)

Preserve the hierarchical structure and all content text."""
                    },
                    {
                        "role": "user",
                        "content": f"""Parse this article content into structured format:

Article {article.article_number}: {article.title}

Content:
{raw_content}

Return structured paragraphs with their subparagraphs and points."""
                    }
                ]
            )

            # Update the result with article info
            result.article_number = article.article_number
            result.title = article.title
            result.extraction_method = "llm"
            result.raw_content = raw_content

            return result

        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return ArticleContent(
                article_number=article.article_number,
                title=article.title,
                paragraphs=[],
                extraction_method="failed",
                raw_content=raw_content
            )

    def validate_content_structure(self, content: ArticleContent) -> dict:
        """
        Validate the structure of extracted content.

        Args:
            content: Extracted article content

        Returns:
            Dictionary with validation results
        """
        total_paragraphs = len(content.paragraphs)
        total_subparagraphs = sum(len(p.subparagraphs) for p in content.paragraphs)
        total_points = sum(len(sp.points) for p in content.paragraphs for sp in p.subparagraphs)

        # Check for sequential numbering
        paragraph_nums = [p.num for p in content.paragraphs]
        expected_nums = [str(i) for i in range(1, len(paragraph_nums) + 1)]
        is_sequential = paragraph_nums == expected_nums

        return {
            "article_number": content.article_number,
            "extraction_method": content.extraction_method,
            "total_paragraphs": total_paragraphs,
            "total_subparagraphs": total_subparagraphs,
            "total_points": total_points,
            "is_sequential": is_sequential,
            "paragraph_numbers": paragraph_nums,
            "has_content": total_paragraphs > 0 or bool(content.raw_content)
        }