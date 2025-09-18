"""
Paragraph extraction from article content with hierarchical structure support.

Handles complex paragraph structures found in EU legal documents:
- Numbered paragraphs (1., 2., 3.)
- Lettered sub-paragraphs ((a), (b), (c))
- Roman numeral sub-points ((i), (ii), (iii))
- Introductory text (no numbering)
"""

import re
from typing import List, Optional, Tuple
from .models import ParagraphInfo


class ParagraphExtractor:
    """Extracts structured paragraphs from raw article content"""

    def __init__(self):
        # Patterns for different paragraph types
        self.numbered_pattern = re.compile(r'^(\d+)\.\s+(.+)', re.MULTILINE | re.DOTALL)
        self.lettered_pattern = re.compile(r'^\s*\(([a-z])\)\s+(.+)', re.MULTILINE | re.DOTALL)
        self.roman_pattern = re.compile(r'^\s*\(([ivx]+)\)\s+(.+)', re.MULTILINE | re.DOTALL)
        self.point_pattern = re.compile(r'^\s*[-–—]\s+(.+)', re.MULTILINE | re.DOTALL)

    def extract_paragraphs(self, raw_content: str, article_number: int) -> List[ParagraphInfo]:
        """
        Extract structured paragraphs from raw article content.

        Args:
            raw_content: Raw text content of the article
            article_number: Article number for context

        Returns:
            List of ParagraphInfo objects with hierarchical structure
        """
        if not raw_content:
            return []

        # Clean and prepare content
        lines = self._clean_content(raw_content, article_number)

        if not lines:
            return []

        # Extract paragraphs using hierarchical approach
        paragraphs = self._extract_hierarchical_paragraphs(lines)

        return paragraphs

    def _clean_content(self, raw_content: str, article_number: int) -> List[str]:
        """
        Clean raw content and prepare for paragraph extraction.

        Args:
            raw_content: Raw text content
            article_number: Article number

        Returns:
            List of cleaned content lines
        """
        lines = raw_content.split('\n')
        cleaned_lines = []

        # Skip article header (Article N and title)
        skip_lines = 0
        for i, line in enumerate(lines[:3]):
            line_clean = line.strip()
            if f"Article {article_number}" in line_clean:
                skip_lines = max(skip_lines, i + 1)
            elif i == skip_lines and len(line_clean) < 100 and line_clean:
                # This is likely the title
                skip_lines = i + 1

        # Process remaining lines
        for line in lines[skip_lines:]:
            line = line.strip()
            if line:
                # Remove page footers, headers, and references
                if self._is_content_line(line):
                    cleaned_lines.append(line)

        return cleaned_lines

    def _is_content_line(self, line: str) -> bool:
        """
        Check if a line contains actual article content.

        Args:
            line: Line to check

        Returns:
            True if line contains content, False if it's metadata/footer
        """
        line = line.strip()

        # Skip empty lines
        if not line:
            return False

        # Skip page references and document metadata
        skip_patterns = [
            r'ELI:\s*http',
            r'\d+/\d+\s*$',  # Page numbers like "7/29"
            r'^EN\s*$',
            r'^OJ\s+L,',
            r'^\(\d+\)\s+Regulation \(EU\)',  # References to other regulations
            r'^\(\d+\)\s+Directive \(EU\)',   # References to other directives
        ]

        for pattern in skip_patterns:
            if re.search(pattern, line):
                return False

        return True

    def _extract_hierarchical_paragraphs(self, lines: List[str]) -> List[ParagraphInfo]:
        """
        Extract paragraphs with hierarchical structure.

        Args:
            lines: Cleaned content lines

        Returns:
            List of ParagraphInfo with proper hierarchy
        """
        if not lines:
            return []

        paragraphs = []
        current_text = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check for numbered paragraph (1., 2., 3.) or ((1), (2), (3))
            numbered_match = re.match(r'^(\d+)\.\s+(.+)', line)
            numbered_paren_match = re.match(r'^\((\d+)\)\s+(.+)', line)

            if numbered_match or numbered_paren_match:
                # Save any accumulated introductory text
                if current_text:
                    intro_para = ParagraphInfo(
                        content=' '.join(current_text),
                        level=1,
                        is_introductory=True
                    )
                    paragraphs.append(intro_para)
                    current_text = []

                # Extract numbered paragraph with potential sub-paragraphs
                if numbered_match:
                    para_num = numbered_match.group(1)
                    para_content = numbered_match.group(2)
                    para_display_num = para_num  # Display as "1", "2", etc.
                else:  # numbered_paren_match
                    para_num = numbered_paren_match.group(1)
                    para_content = numbered_paren_match.group(2)
                    para_display_num = f"({para_num})"  # Display as "(1)", "(2)", etc.

                # Look ahead for continuation and sub-paragraphs
                para_lines = [para_content]
                sub_paragraphs = []
                i += 1

                while i < len(lines):
                    next_line = lines[i].strip()

                    # Check if this is a sub-paragraph (a), (b), (c)
                    letter_match = re.match(r'^\(([a-z])\)\s+(.+)', next_line)
                    if letter_match:
                        sub_para = self._extract_sub_paragraph(lines, i, level=2)
                        if sub_para:
                            sub_paragraphs.append(sub_para[0])
                            i = sub_para[1]  # Update index
                        else:
                            i += 1
                    # Check if this is start of next numbered paragraph
                    elif re.match(r'^\d+\.\s+', next_line) or re.match(r'^\(\d+\)\s+', next_line):
                        break
                    # Check if this is continuation of current paragraph
                    elif not re.match(r'^\(.*\)', next_line) and next_line:
                        para_lines.append(next_line)
                        i += 1
                    else:
                        i += 1

                # Create paragraph
                paragraph = ParagraphInfo(
                    paragraph_number=para_display_num,
                    content=' '.join(para_lines),
                    level=1,
                    sub_paragraphs=sub_paragraphs
                )
                paragraphs.append(paragraph)
                continue

            # Accumulate text for potential introductory paragraph
            if line:
                current_text.append(line)

            i += 1

        # Handle any remaining text as introductory paragraph
        if current_text:
            intro_para = ParagraphInfo(
                content=' '.join(current_text),
                level=1,
                is_introductory=True
            )
            paragraphs.append(intro_para)

        return paragraphs

    def _extract_sub_paragraph(self, lines: List[str], start_idx: int, level: int) -> Optional[Tuple[ParagraphInfo, int]]:
        """
        Extract a sub-paragraph starting at the given index.

        Args:
            lines: All content lines
            start_idx: Index to start extraction
            level: Hierarchy level (2 for (a), 3 for (i))

        Returns:
            Tuple of (ParagraphInfo, next_index) or None
        """
        if start_idx >= len(lines):
            return None

        line = lines[start_idx].strip()

        # Determine pattern based on level
        if level == 2:
            # Level 2: (a), (b), (c)
            match = re.match(r'^\(([a-z])\)\s+(.+)', line)
        else:
            # Level 3: (i), (ii), (iii)
            match = re.match(r'^\(([ivx]+)\)\s+(.+)', line)

        if not match:
            return None

        para_id = match.group(1)
        para_content = match.group(2)
        para_lines = [para_content]
        sub_paragraphs = []

        i = start_idx + 1

        # Look for continuation and deeper sub-paragraphs
        while i < len(lines):
            next_line = lines[i].strip()

            if level == 2:
                # At level 2, look for level 3 sub-paragraphs (i), (ii)
                roman_match = re.match(r'^\(([ivx]+)\)\s+(.+)', next_line)
                if roman_match:
                    sub_para = self._extract_sub_paragraph(lines, i, level=3)
                    if sub_para:
                        sub_paragraphs.append(sub_para[0])
                        i = sub_para[1]
                    else:
                        i += 1
                # Check for next letter paragraph
                elif re.match(r'^\(([a-z])\)\s+', next_line):
                    break
                # Check for numbered paragraph
                elif re.match(r'^\d+\.\s+', next_line) or re.match(r'^\(\d+\)\s+', next_line):
                    break
                # Continuation text
                elif next_line and not re.match(r'^\(.*\)', next_line):
                    para_lines.append(next_line)
                    i += 1
                else:
                    i += 1
            else:
                # At level 3, just accumulate until next structure
                if (re.match(r'^\(([a-z])\)\s+', next_line) or
                    re.match(r'^\(([ivx]+)\)\s+', next_line) or
                    re.match(r'^\d+\.\s+', next_line) or
                    re.match(r'^\(\d+\)\s+', next_line)):
                    break
                elif next_line:
                    para_lines.append(next_line)
                    i += 1
                else:
                    i += 1

        paragraph = ParagraphInfo(
            paragraph_number=f"({para_id})",
            content=' '.join(para_lines),
            level=level,
            sub_paragraphs=sub_paragraphs
        )

        return (paragraph, i)

    def _roman_to_int(self, roman: str) -> int:
        """Convert roman numerals to integers for sorting."""
        roman_values = {'i': 1, 'v': 5, 'x': 10}
        result = 0
        prev_value = 0

        for char in reversed(roman.lower()):
            value = roman_values.get(char, 0)
            if value < prev_value:
                result -= value
            else:
                result += value
            prev_value = value

        return result

    def get_paragraph_summary(self, paragraphs: List[ParagraphInfo]) -> dict:
        """
        Get summary statistics about extracted paragraphs.

        Args:
            paragraphs: List of ParagraphInfo objects

        Returns:
            Dictionary with summary statistics
        """
        if not paragraphs:
            return {
                "total_paragraphs": 0,
                "numbered_paragraphs": 0,
                "introductory_paragraphs": 0,
                "max_level": 0,
                "has_sub_paragraphs": False
            }

        total = len(paragraphs)
        numbered = sum(1 for p in paragraphs if p.paragraph_number)
        introductory = sum(1 for p in paragraphs if p.is_introductory)
        max_level = max(p.level for p in paragraphs)
        has_sub = any(p.sub_paragraphs for p in paragraphs)

        # Count total sub-paragraphs recursively
        def count_all_paragraphs(paras):
            count = len(paras)
            for para in paras:
                count += count_all_paragraphs(para.sub_paragraphs)
            return count

        total_with_sub = count_all_paragraphs(paragraphs)

        return {
            "total_paragraphs": total,
            "total_with_sub_paragraphs": total_with_sub,
            "numbered_paragraphs": numbered,
            "introductory_paragraphs": introductory,
            "max_level": max_level,
            "has_sub_paragraphs": has_sub,
            "paragraph_structure": [
                {
                    "number": p.paragraph_number,
                    "level": p.level,
                    "is_intro": p.is_introductory,
                    "sub_count": len(p.sub_paragraphs),
                    "content_length": len(p.content)
                }
                for p in paragraphs
            ]
        }