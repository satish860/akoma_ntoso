import instructor
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from typing import List, Optional, Dict
from .models import ArticleInfo, ArticlesInChapter, SectionInfo

load_dotenv()

class ArticleExtractor:
    """LLM-based article extractor using Instructor for reliable parsing"""

    def __init__(self):
        """Initialize with OpenRouter client using GPT-4"""
        self.client = instructor.from_openai(
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        )
        self.model = "openai/gpt-4o-mini"

    def load_chapter_content(self, json_path: str) -> List[Dict]:
        """Load chapter content from JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['chapters']

    def load_sections(self, json_path: str) -> List[SectionInfo]:
        """Load sections from JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        sections = []
        for section_data in data['sections']:
            section = SectionInfo(
                section_number=section_data['section_number'],
                parent_chapter=section_data['parent_chapter'],
                start_line=section_data['start_line'],
                confidence=section_data['confidence']
            )
            sections.append(section)

        return sections

    def extract_articles_from_chapter(self, chapter_content: str, chapter_number: str, chapter_start_line: int) -> ArticlesInChapter:
        """
        Extract articles from a single chapter content using LLM.

        Args:
            chapter_content: Text content of the chapter
            chapter_number: Chapter number (Roman numeral)
            chapter_start_line: Starting line number of the chapter

        Returns:
            ArticlesInChapter with all articles found
        """
        try:
            result = self.client.chat.completions.create(
                model=self.model,
                response_model=ArticlesInChapter,
                messages=[
                    {
                        "role": "system",
                        "content": """You are analyzing EU regulation text to identify ARTICLE HEADERS ONLY.

CRITICAL RULES FOR ARTICLE IDENTIFICATION:

✅ VALID Article Headers (INCLUDE these):
- Line contains ONLY "Article [number]" (no other text on that line)
- The article number is a simple integer (1, 2, 3, etc.)
- The next line contains the article title
- Examples of VALID headers:
  "Article 1"
  "Subject matter"

  "Article 5"
  "Governance and organisation"

❌ INVALID Article References (EXCLUDE these):
- "in accordance with Article X"
- "referred to in Article X"
- "pursuant to Article X"
- "Article 2(1), points (a) to (d)"
- "Article 6(4)"
- Any line where "Article X" is part of a sentence or has parentheses

PATTERN TO IDENTIFY:
1. The line must be EXACTLY "Article [number]" with no other text
2. The following line must be the article title
3. Article numbers should be sequential integers within the chapter
4. Do NOT include any references to articles within sentences
5. Do NOT include article references with subsection numbers like "Article 2(1)"

IMPORTANT:
- Only count standalone "Article N" headers, not references
- Be very conservative - if unsure, DO NOT include it
- Article titles are usually 2-10 words describing the article's purpose"""
                    },
                    {
                        "role": "user",
                        "content": f"""Find ONLY the actual article headers in this chapter content.

Chapter: {chapter_number}

{chapter_content}

For each REAL article header found:
1. Verify it's a standalone "Article [number]" line (no other text)
2. Confirm the next line is a title (not part of a sentence)
3. Check the number is a simple integer (not like "Article 2(1)")
4. IGNORE ALL references to articles within sentences

Return:
- chapter_number: "{chapter_number}"
- articles: List of articles with article_number, title, and start_line (relative position)
- has_articles: Whether any valid articles were found

For start_line: Count line by line from the start of the content (0-based).
Be very conservative - only include if you're 100% certain it's a real header."""
                    }
                ]
            )

            # Convert relative line positions to actual line numbers
            for article in result.articles:
                article.start_line = chapter_start_line + article.start_line
                article.parent_chapter = chapter_number
                # parent_section will be assigned later based on line boundaries

            return result

        except Exception as e:
            print(f"Error extracting articles from Chapter {chapter_number}: {e}")
            print(f"API Key present: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")
            return ArticlesInChapter(
                chapter_number=chapter_number,
                articles=[],
                has_articles=False
            )

    def assign_parent_sections(self, articles: List[ArticleInfo], sections: List[SectionInfo]) -> None:
        """
        Assign parent_section to articles based on line boundaries.

        Args:
            articles: List of articles to assign sections to (modified in place)
            sections: List of sections with their boundaries
        """
        # Group sections by chapter
        sections_by_chapter = {}
        for section in sections:
            chapter = section.parent_chapter
            if chapter not in sections_by_chapter:
                sections_by_chapter[chapter] = []
            sections_by_chapter[chapter].append(section)

        # Sort sections within each chapter by start line
        for chapter_num in sections_by_chapter:
            sections_by_chapter[chapter_num].sort(key=lambda s: s.start_line)

        # Assign parent sections
        for article in articles:
            chapter = article.parent_chapter
            chapter_sections = sections_by_chapter.get(chapter, [])

            if chapter_sections:
                # This chapter has sections, find which section contains this article
                article.parent_section = self._find_parent_section(article, chapter_sections)
            else:
                # This chapter has no sections, article goes directly under chapter
                article.parent_section = None

    def _find_parent_section(self, article: ArticleInfo, sections: List[SectionInfo]) -> Optional[str]:
        """
        Find which section an article belongs to based on line boundaries.

        Args:
            article: ArticleInfo to assign
            sections: List of sections in the same chapter, sorted by start_line

        Returns:
            Section number if found, None if article doesn't fall within any section
        """
        article_line = article.start_line

        for i, section in enumerate(sections):
            # Determine section boundaries
            section_start = section.start_line

            # End of section is either start of next section or end of document
            if i + 1 < len(sections):
                section_end = sections[i + 1].start_line - 1
            else:
                section_end = float('inf')  # Last section goes to end of chapter

            # Check if article falls within this section
            if section_start <= article_line <= section_end:
                return section.section_number

        return None

    def extract_all_articles(self, chapters_json_path: str, sections_json_path: str) -> List[ArticleInfo]:
        """
        Extract all articles from all chapters with proper section assignment.
        Uses hybrid approach: LLM for article identification + pattern matching for accurate line numbers.

        Args:
            chapters_json_path: Path to chapters content JSON
            sections_json_path: Path to sections JSON

        Returns:
            List of all ArticleInfo with proper parent_chapter and parent_section
        """
        print("=== Article Extraction with Instructor (Hybrid Approach) ===")

        # Load data
        chapters_data = self.load_chapter_content(chapters_json_path)
        sections = self.load_sections(sections_json_path)

        print(f"Loaded {len(chapters_data)} chapters and {len(sections)} sections")

        # Step 1: Use LLM to identify articles and get titles
        print(f"\n--- Step 1: LLM Article Identification ---")
        llm_articles = []

        for chapter_data in chapters_data:
            chapter_number = chapter_data['chapter_number']
            chapter_content = chapter_data['content']
            chapter_start_line = chapter_data['start_line']

            print(f"\nProcessing Chapter {chapter_number}: {chapter_data['title']}")

            # Extract articles using LLM (for titles)
            articles_in_chapter = self.extract_articles_from_chapter(
                chapter_content,
                chapter_number,
                chapter_start_line
            )

            if articles_in_chapter.has_articles:
                print(f"LLM found {len(articles_in_chapter.articles)} articles:")
                for article in articles_in_chapter.articles:
                    print(f"  Article {article.article_number}: {article.title}")

                llm_articles.extend(articles_in_chapter.articles)
            else:
                print("No articles found by LLM")

        # Step 2: Use pattern matching to get accurate line numbers
        print(f"\n--- Step 2: Pattern Matching for Accurate Line Numbers ---")
        corrected_articles = self._correct_line_numbers_with_pattern_matching(llm_articles, chapters_data)

        # Step 3: Assign parent sections
        print(f"\n--- Step 3: Assigning Parent Sections ---")
        self.assign_parent_sections(corrected_articles, sections)

        # Show final assignment
        print(f"\n--- Final Article Assignment ---")
        for article in sorted(corrected_articles, key=lambda a: (a.parent_chapter, a.article_number)):
            section_info = f"Section {article.parent_section}" if article.parent_section else "Direct under chapter"
            print(f"Article {article.article_number} in Chapter {article.parent_chapter}: {section_info}")

        print(f"\nTotal articles extracted: {len(corrected_articles)}")
        return corrected_articles

    def _correct_line_numbers_with_pattern_matching(self, llm_articles: List[ArticleInfo], chapters_data: List[dict]) -> List[ArticleInfo]:
        """
        Correct line numbers using pattern matching in PDF.

        Args:
            llm_articles: Articles identified by LLM (may have wrong line numbers)
            chapters_data: Chapter data with boundaries

        Returns:
            Articles with corrected line numbers
        """
        from ..pdf_extractor import extract_text_with_line_numbers

        print("Loading PDF for pattern matching...")

        # Load PDF content
        pdf_text, _ = extract_text_with_line_numbers("data/dora/level1/DORA_Regulation_EU_2022_2554.pdf")
        pdf_lines = {}
        for line in pdf_text.split('\n'):
            if ': ' in line:
                parts = line.split(': ', 1)
                try:
                    line_num = int(parts[0])
                    content = parts[1] if len(parts) > 1 else ""
                    pdf_lines[line_num] = content
                except ValueError:
                    continue

        print(f"Loaded {len(pdf_lines)} lines from PDF")

        # Find all article patterns in PDF
        pdf_articles = {}
        for line_num, content in pdf_lines.items():
            if content.strip().startswith("Article ") and len(content.strip().split()) == 2:
                try:
                    article_num = int(content.strip().split()[1])
                    pdf_articles[article_num] = line_num
                except ValueError:
                    pass

        print(f"Found {len(pdf_articles)} article patterns in PDF")

        # Create chapter boundaries
        chapter_boundaries = {}
        sorted_chapters = sorted(chapters_data, key=lambda ch: ch['start_line'])
        for i, chapter in enumerate(sorted_chapters):
            chapter_num = chapter['chapter_number']
            start_line = chapter['start_line']
            end_line = sorted_chapters[i + 1]['start_line'] - 1 if i + 1 < len(sorted_chapters) else 999999
            chapter_boundaries[chapter_num] = (start_line, end_line)

        # Correct line numbers
        corrected_articles = []
        corrections_made = 0

        for article in llm_articles:
            corrected_article = ArticleInfo(
                article_number=article.article_number,
                title=article.title,
                start_line=article.start_line,  # Will be corrected below
                parent_chapter=article.parent_chapter,
                parent_section=None,  # Will be assigned later
                confidence=article.confidence
            )

            # Check if we have exact line number from pattern matching
            if article.article_number in pdf_articles:
                pdf_line = pdf_articles[article.article_number]
                chapter_bounds = chapter_boundaries.get(article.parent_chapter, (0, 999999))

                # Verify article is within expected chapter boundaries
                if chapter_bounds[0] <= pdf_line <= chapter_bounds[1]:
                    if pdf_line != article.start_line:
                        print(f"  Corrected Article {article.article_number}: {article.start_line} -> {pdf_line}")
                        corrections_made += 1
                    corrected_article.start_line = pdf_line
                    corrected_article.confidence = 95  # High confidence for pattern match
                else:
                    print(f"  Warning: Article {article.article_number} at line {pdf_line} outside Chapter {article.parent_chapter} bounds")
            else:
                print(f"  Warning: No pattern match found for Article {article.article_number}")

            corrected_articles.append(corrected_article)

        print(f"Made {corrections_made} line number corrections")

        # Step 4: Extract article content
        print(f"\n--- Step 4: Extracting Article Content ---")
        articles_with_content = self._extract_article_content(corrected_articles, pdf_lines)

        return articles_with_content

    def _extract_article_content(self, articles: List[ArticleInfo], pdf_lines: dict) -> List[ArticleInfo]:
        """
        Extract the actual content of each article using line boundaries.

        Args:
            articles: Articles with correct line numbers
            pdf_lines: Dictionary mapping line numbers to content

        Returns:
            Articles with content extracted
        """
        print("Extracting article content...")

        # Sort articles by line number to determine boundaries
        sorted_articles = sorted(articles, key=lambda a: a.start_line)

        for i, article in enumerate(sorted_articles):
            # Determine end line for this article
            if i + 1 < len(sorted_articles):
                end_line = sorted_articles[i + 1].start_line - 1
            else:
                end_line = max(pdf_lines.keys())  # Last article goes to end

            # Extract content from start_line to end_line
            content_lines = []
            for line_num in range(article.start_line, end_line + 1):
                if line_num in pdf_lines:
                    content_lines.append(pdf_lines[line_num])

            # Store content in article (we'll add this to the model)
            article.raw_content = '\n'.join(content_lines)

            print(f"  Article {article.article_number}: {len(content_lines)} lines of content")

        return articles

    def validate_articles(self, articles: List[ArticleInfo]) -> Dict:
        """
        Validate extracted articles for consistency.

        Args:
            articles: List of articles to validate

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

        validation = {
            "total_articles": len(articles),
            "chapters_with_articles": list(articles_by_chapter.keys()),
            "articles_by_chapter": {},
            "articles_with_sections": 0,
            "articles_without_sections": 0,
            "validation_issues": []
        }

        for chapter, chapter_articles in articles_by_chapter.items():
            # Sort by article number
            sorted_articles = sorted(chapter_articles, key=lambda art: art.article_number)
            article_numbers = [art.article_number for art in sorted_articles]

            # Check for sequential numbering (starting from 1)
            expected_sequence = list(range(1, len(article_numbers) + 1))
            is_sequential = article_numbers == expected_sequence

            # Count section assignments
            with_sections = len([art for art in chapter_articles if art.parent_section])
            without_sections = len([art for art in chapter_articles if not art.parent_section])

            validation["articles_by_chapter"][chapter] = {
                "count": len(chapter_articles),
                "article_numbers": article_numbers,
                "is_sequential": is_sequential,
                "with_sections": with_sections,
                "without_sections": without_sections
            }

            validation["articles_with_sections"] += with_sections
            validation["articles_without_sections"] += without_sections

            # Check for validation issues
            if not is_sequential:
                validation["validation_issues"].append(f"Chapter {chapter}: Non-sequential numbering {article_numbers}")

            # Check for duplicates
            if len(article_numbers) != len(set(article_numbers)):
                validation["validation_issues"].append(f"Chapter {chapter}: Duplicate article numbers")

        return validation