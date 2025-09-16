from typing import List
from .models import ChapterInfo, SectionInfo

def build_chapters_xml(chapters: List[ChapterInfo]) -> str:
    """
    Build Akoma Ntoso XML structure for chapters.

    Args:
        chapters: List of ChapterInfo objects

    Returns:
        XML string with proper chapter structure
    """
    if not chapters:
        return "    <body>\n      <!-- No chapters found -->\n    </body>"

    # Sort chapters by line number to ensure proper order
    sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

    xml_parts = ["    <body>"]

    for chapter in sorted_chapters:
        # Create chapter ID from Roman numeral (e.g., "chp_I", "chp_II")
        chapter_id = f"chp_{chapter.chapter_number}"

        xml_parts.extend([
            f'      <chapter id="{chapter_id}">',
            f'        <num>CHAPTER {chapter.chapter_number}</num>',
            f'        <heading>{chapter.title}</heading>',
            '      </chapter>'
        ])

    xml_parts.append("    </body>")

    return '\n'.join(xml_parts)

def get_chapters_summary(chapters: List[ChapterInfo]) -> dict:
    """
    Get summary statistics about the chapters.

    Args:
        chapters: List of ChapterInfo objects

    Returns:
        Dictionary with summary statistics
    """
    if not chapters:
        return {
            "count": 0,
            "first_chapter": None,
            "last_chapter": None,
            "pages_span": 0,
            "confidence_avg": 0,
            "chapter_sequence": [],
            "line_range": (0, 0)
        }

    # Sort by line number
    sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

    pages = [ch.page_number for ch in chapters]
    confidences = [ch.confidence for ch in chapters]

    return {
        "count": len(chapters),
        "first_chapter": sorted_chapters[0].chapter_number,
        "last_chapter": sorted_chapters[-1].chapter_number,
        "pages_span": max(pages) - min(pages) + 1,
        "confidence_avg": sum(confidences) // len(confidences),
        "chapter_sequence": [ch.chapter_number for ch in sorted_chapters],
        "line_range": (sorted_chapters[0].start_line, sorted_chapters[-1].start_line)
    }

def validate_chapter_xml(xml_content: str) -> dict:
    """
    Basic validation of generated chapter XML.

    Args:
        xml_content: Generated XML string

    Returns:
        Dictionary with validation results
    """
    validation = {
        "has_body": "<body>" in xml_content,
        "has_chapters": "<chapter" in xml_content,
        "chapter_count": xml_content.count("<chapter"),
        "has_headings": "<heading>" in xml_content,
        "has_nums": "<num>" in xml_content,
        "is_well_formed": True  # Basic check
    }

    # Check if all chapters have required elements
    chapter_count = validation["chapter_count"]
    heading_count = xml_content.count("<heading>")
    num_count = xml_content.count("<num>")

    validation["all_chapters_complete"] = (
        chapter_count == heading_count == num_count
    )

    return validation

def build_chapters_with_sections_xml(chapters: List[ChapterInfo], sections: List[SectionInfo]) -> str:
    """
    Build Akoma Ntoso XML structure for chapters with sections nested inside.

    Args:
        chapters: List of ChapterInfo objects
        sections: List of SectionInfo objects

    Returns:
        XML string with proper chapter and section structure
    """
    if not chapters:
        return "    <body>\n      <!-- No chapters found -->\n    </body>"

    # Sort chapters and group sections by chapter
    sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)
    sections_by_chapter = {}

    for section in sections:
        if section.parent_chapter not in sections_by_chapter:
            sections_by_chapter[section.parent_chapter] = []
        sections_by_chapter[section.parent_chapter].append(section)

    # Sort sections within each chapter by start line
    for chapter_num in sections_by_chapter:
        sections_by_chapter[chapter_num].sort(key=lambda s: s.start_line)

    xml_parts = ["    <body>"]

    for chapter in sorted_chapters:
        # Create chapter ID from Roman numeral (e.g., "chp_I", "chp_II")
        chapter_id = f"chp_{chapter.chapter_number}"

        xml_parts.extend([
            f'      <chapter id="{chapter_id}">',
            f'        <num>CHAPTER {chapter.chapter_number}</num>',
            f'        <heading>{chapter.title}</heading>'
        ])

        # Add sections if this chapter has any
        chapter_sections = sections_by_chapter.get(chapter.chapter_number, [])

        if chapter_sections:
            # Chapter has sections
            for section in chapter_sections:
                section_id = f"sec_{chapter.chapter_number}_{section.section_number}"
                xml_parts.extend([
                    f'        <section id="{section_id}">',
                    f'          <num>Section {section.section_number}</num>',
                    '        </section>'
                ])
        else:
            # Chapter has no sections - add placeholder comment
            xml_parts.append('        <!-- No sections in this chapter -->')

        xml_parts.append('      </chapter>')

    xml_parts.append("    </body>")

    return '\n'.join(xml_parts)