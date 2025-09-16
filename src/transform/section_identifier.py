import re
from typing import List
from .models import SectionInfo, ChapterInfo
from ..pdf_extractor import extract_lines_range


class SectionIdentifier:
    """Simple section identifier for EU regulations"""

    def __init__(self):
        """Initialize with regex pattern for sections"""
        self.section_pattern = re.compile(r'^Section ([IVX]+)', re.MULTILINE)

    def extract_sections_within_chapters(self, pdf_path: str, chapters: List[ChapterInfo]) -> List[SectionInfo]:
        """
        Extract all sections within the given chapters.

        Args:
            pdf_path: Path to PDF file
            chapters: List of ChapterInfo objects

        Returns:
            List of SectionInfo objects found within chapters
        """
        if not chapters:
            return []

        all_sections = []
        print(f"Extracting sections within {len(chapters)} chapters...")

        # Sort chapters by start_line to determine boundaries
        sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

        for i, chapter in enumerate(sorted_chapters):
            # Determine chapter end line
            if i < len(sorted_chapters) - 1:
                chapter_end_line = sorted_chapters[i + 1].start_line - 1
            else:
                chapter_end_line = 999999  # Large number for last chapter

            print(f"  Processing Chapter {chapter.chapter_number} (lines {chapter.start_line}-{chapter_end_line})...")

            # Extract content for this chapter
            try:
                chapter_content = extract_lines_range(pdf_path, chapter.start_line, chapter_end_line)

                if not chapter_content.strip():
                    print(f"    No content found for Chapter {chapter.chapter_number}")
                    continue

                # Find sections within this chapter
                sections = self._find_sections_in_content(
                    chapter_content,
                    chapter.chapter_number,
                    chapter.start_line
                )

                if sections:
                    print(f"    Found {len(sections)} section(s): {[s.section_number for s in sections]}")
                    all_sections.extend(sections)
                else:
                    print(f"    No sections found in Chapter {chapter.chapter_number}")

            except Exception as e:
                print(f"    Error processing Chapter {chapter.chapter_number}: {e}")

        print(f"\nTotal sections found: {len(all_sections)}")
        return all_sections

    def _find_sections_in_content(self, content: str, parent_chapter: str, chapter_start_line: int) -> List[SectionInfo]:
        """
        Find sections within chapter content using regex.

        Args:
            content: Chapter content text
            parent_chapter: Parent chapter number
            chapter_start_line: Starting line number of the chapter

        Returns:
            List of SectionInfo objects found in content
        """
        sections = []
        lines = content.split('\n')

        for line_idx, line in enumerate(lines):
            line = line.strip()
            match = self.section_pattern.match(line)

            if match:
                section_number = match.group(1)

                # Calculate actual line number in document
                actual_line = chapter_start_line + line_idx

                section = SectionInfo(
                    section_number=section_number,
                    parent_chapter=parent_chapter,
                    start_line=actual_line,
                    confidence=100  # High confidence for regex match
                )

                sections.append(section)

        return sections

    def validate_sections(self, sections: List[SectionInfo]) -> dict:
        """
        Validate extracted sections for consistency.

        Args:
            sections: List of SectionInfo objects

        Returns:
            Dictionary with validation results
        """
        validation = {
            "total_sections": len(sections),
            "sections_by_chapter": {},
            "section_numbers": [s.section_number for s in sections],
            "chapters_with_sections": set()
        }

        # Group by chapter
        for section in sections:
            chapter = section.parent_chapter
            if chapter not in validation["sections_by_chapter"]:
                validation["sections_by_chapter"][chapter] = []
            validation["sections_by_chapter"][chapter].append(section.section_number)
            validation["chapters_with_sections"].add(chapter)

        validation["chapters_with_sections"] = list(validation["chapters_with_sections"])

        return validation