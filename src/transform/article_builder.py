from typing import List, Dict
from .models import ArticleInfo, ChapterInfo, SectionInfo

def build_hierarchical_xml(
    chapters: List[ChapterInfo],
    sections: List[SectionInfo],
    articles: List[ArticleInfo]
) -> str:
    """
    Build complete Akoma Ntoso XML hierarchy: Chapters → Sections (optional) → Articles

    Args:
        chapters: List of ChapterInfo objects
        sections: List of SectionInfo objects
        articles: List of ArticleInfo objects

    Returns:
        XML string with complete hierarchical structure
    """
    if not chapters:
        return "    <body>\n      <!-- No chapters found -->\n    </body>"

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

    # Group articles by chapter and section
    articles_by_chapter = {}
    articles_by_section = {}

    for article in articles:
        chapter = article.parent_chapter
        section = article.parent_section

        # Group by chapter
        if chapter not in articles_by_chapter:
            articles_by_chapter[chapter] = []
        articles_by_chapter[chapter].append(article)

        # Group by section if article has a parent section
        if section:
            section_key = f"{chapter}_{section}"
            if section_key not in articles_by_section:
                articles_by_section[section_key] = []
            articles_by_section[section_key].append(article)

    # Sort chapters by start line
    sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

    xml_parts = ["    <body>"]

    for chapter in sorted_chapters:
        chapter_id = f"chp_{chapter.chapter_number}"

        xml_parts.extend([
            f'      <chapter id="{chapter_id}">',
            f'        <num>CHAPTER {chapter.chapter_number}</num>',
            f'        <heading>{chapter.title}</heading>'
        ])

        # Check if this chapter has sections
        chapter_sections = sections_by_chapter.get(chapter.chapter_number, [])

        if chapter_sections:
            # Chapter has sections - nest articles under sections
            for section in chapter_sections:
                section_id = f"sec_{chapter.chapter_number}_{section.section_number}"

                xml_parts.extend([
                    f'        <section id="{section_id}">',
                    f'          <num>Section {section.section_number}</num>'
                ])

                # Add articles for this section
                section_key = f"{chapter.chapter_number}_{section.section_number}"
                section_articles = articles_by_section.get(section_key, [])

                if section_articles:
                    # Sort articles by article number
                    sorted_articles = sorted(section_articles, key=lambda art: art.article_number)

                    for article in sorted_articles:
                        article_xml = build_article_xml(article)
                        # Indent article XML properly within section
                        indented_article = '\n'.join('          ' + line for line in article_xml.split('\n') if line.strip())
                        xml_parts.append(indented_article)
                else:
                    xml_parts.append('          <!-- No articles in this section -->')

                xml_parts.append('        </section>')
        else:
            # Chapter has no sections - articles go directly under chapter
            chapter_articles = articles_by_chapter.get(chapter.chapter_number, [])

            if chapter_articles:
                # Filter articles that don't have a parent section (they belong directly to chapter)
                direct_articles = [art for art in chapter_articles if not art.parent_section]

                if direct_articles:
                    # Sort articles by article number
                    sorted_articles = sorted(direct_articles, key=lambda art: art.article_number)

                    for article in sorted_articles:
                        article_xml = build_article_xml(article)
                        # Indent article XML properly within chapter
                        indented_article = '\n'.join('        ' + line for line in article_xml.split('\n') if line.strip())
                        xml_parts.append(indented_article)
                else:
                    xml_parts.append('        <!-- No direct articles in this chapter -->')
            else:
                xml_parts.append('        <!-- No articles in this chapter -->')

        xml_parts.append('      </chapter>')

    xml_parts.append("    </body>")

    return '\n'.join(xml_parts)

def build_article_xml(article: ArticleInfo) -> str:
    """
    Build XML structure for a single article with full content.

    Args:
        article: ArticleInfo object with raw_content

    Returns:
        XML string for the article
    """
    article_id = f"art_{article.article_number}"

    xml_parts = [
        f'<article id="{article_id}">',
        f'  <num>{article.article_number}</num>',
        f'  <heading>{escape_xml(article.title)}</heading>'
    ]

    # Parse and add article content
    if article.raw_content:
        content_xml = parse_article_content(article.raw_content, article.article_number)
        # Indent content properly
        indented_content = '\n'.join('  ' + line for line in content_xml.split('\n') if line.strip())
        xml_parts.append(indented_content)
    else:
        xml_parts.append('  <!-- No content available -->')

    xml_parts.append('</article>')

    return '\n'.join(xml_parts)

def parse_article_content(raw_content: str, article_number: int) -> str:
    """
    Parse raw article content into structured XML paragraphs.

    Args:
        raw_content: Raw text content of the article
        article_number: Article number for context

    Returns:
        XML string with structured content
    """
    if not raw_content:
        return '<!-- No content -->'

    lines = raw_content.split('\n')
    xml_parts = []

    # Skip the article header (first 1-2 lines usually contain "Article N" and title)
    content_start = 0
    for i, line in enumerate(lines[:3]):
        if f"Article {article_number}" in line or (i == 1 and len(line.strip()) < 100):
            content_start = i + 1
        elif line.strip() and not line.startswith('Article'):
            break

    content_lines = lines[content_start:]

    # Group lines into paragraphs
    paragraphs = []
    current_paragraph = []

    for line in content_lines:
        line = line.strip()
        if not line:
            # Empty line - end current paragraph if it has content
            if current_paragraph:
                paragraphs.append('\n'.join(current_paragraph))
                current_paragraph = []
        else:
            current_paragraph.append(line)

    # Add the last paragraph if it exists
    if current_paragraph:
        paragraphs.append('\n'.join(current_paragraph))

    # Convert paragraphs to XML
    for i, para_text in enumerate(paragraphs[:10]):  # Limit to first 10 paragraphs for now
        if para_text.strip():
            # Check if it's a numbered paragraph (starts with number)
            if para_text.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                # This is likely a numbered paragraph
                para_num = para_text.split('.')[0]
                para_content = para_text[len(para_num)+1:].strip()
                xml_parts.extend([
                    f'<paragraph id="art_{article_number}_par_{para_num}">',
                    f'  <num>{para_num}</num>',
                    f'  <content>',
                    f'    <p>{escape_xml(para_content[:500])}{"..." if len(para_content) > 500 else ""}</p>',
                    f'  </content>',
                    f'</paragraph>'
                ])
            else:
                # Regular paragraph or content
                xml_parts.extend([
                    f'<paragraph id="art_{article_number}_par_{i+1}">',
                    f'  <content>',
                    f'    <p>{escape_xml(para_text[:500])}{"..." if len(para_text) > 500 else ""}</p>',
                    f'  </content>',
                    f'</paragraph>'
                ])

    if not xml_parts:
        xml_parts.append('<!-- No structured content found -->')

    return '\n'.join(xml_parts)

def escape_xml(text: str) -> str:
    """
    Escape special XML characters in content.

    Args:
        text: Text to escape

    Returns:
        XML-escaped text
    """
    if not text:
        return ""

    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))

def get_hierarchy_summary(chapters: List[ChapterInfo], sections: List[SectionInfo], articles: List[ArticleInfo]) -> dict:
    """
    Get summary statistics about the complete hierarchy.

    Args:
        chapters: List of ChapterInfo objects
        sections: List of SectionInfo objects
        articles: List of ArticleInfo objects

    Returns:
        Dictionary with hierarchy summary statistics
    """
    # Group sections by chapter
    sections_by_chapter = {}
    for section in sections:
        chapter = section.parent_chapter
        if chapter not in sections_by_chapter:
            sections_by_chapter[chapter] = []
        sections_by_chapter[chapter].append(section)

    # Group articles by chapter and section
    articles_by_chapter = {}
    articles_by_section = {}

    for article in articles:
        chapter = article.parent_chapter
        section = article.parent_section

        # Group by chapter
        if chapter not in articles_by_chapter:
            articles_by_chapter[chapter] = []
        articles_by_chapter[chapter].append(article)

        # Group by section if applicable
        if section:
            section_key = f"{chapter}_{section}"
            if section_key not in articles_by_section:
                articles_by_section[section_key] = []
            articles_by_section[section_key].append(article)

    chapters_with_sections = list(sections_by_chapter.keys())
    chapters_without_sections = [ch.chapter_number for ch in chapters if ch.chapter_number not in chapters_with_sections]

    return {
        "total_chapters": len(chapters),
        "total_sections": len(sections),
        "total_articles": len(articles),
        "chapters_with_sections": chapters_with_sections,
        "chapters_without_sections": chapters_without_sections,
        "articles_by_chapter": {ch: len(articles_by_chapter.get(ch, [])) for ch in [c.chapter_number for c in chapters]},
        "articles_by_section": {key: len(arts) for key, arts in articles_by_section.items()},
        "articles_under_sections": len([art for art in articles if art.parent_section]),
        "articles_under_chapters": len([art for art in articles if not art.parent_section])
    }

def validate_hierarchy_xml(xml_content: str) -> dict:
    """
    Basic validation of generated hierarchical XML.

    Args:
        xml_content: Generated XML string

    Returns:
        Dictionary with validation results
    """
    validation = {
        "has_body": "<body>" in xml_content,
        "has_chapters": "<chapter" in xml_content,
        "has_sections": "<section" in xml_content,
        "has_articles": "<article" in xml_content,
        "chapter_count": xml_content.count("<chapter"),
        "section_count": xml_content.count("<section"),
        "article_count": xml_content.count("<article"),
        "has_article_headings": xml_content.count("<heading>") >= xml_content.count("<article"),
        "has_article_nums": xml_content.count("<num>") >= xml_content.count("<article"),
        "is_well_formed": True  # Basic check
    }

    # Check if all articles have required elements
    article_count = validation["article_count"]
    closed_articles = xml_content.count('</article>')

    validation["all_articles_complete"] = (article_count == closed_articles)

    return validation

def build_chapters_with_articles_xml(chapters: List[ChapterInfo], articles: List[ArticleInfo]) -> str:
    """
    Build XML for chapters with articles (without sections).
    Legacy compatibility function.

    Args:
        chapters: List of ChapterInfo objects
        articles: List of ArticleInfo objects

    Returns:
        XML string with chapters containing their articles
    """
    if not chapters:
        return "    <body>\n      <!-- No chapters found -->\n    </body>"

    # Group articles by chapter
    articles_by_chapter = {}
    for article in articles:
        chapter = article.parent_chapter
        if chapter not in articles_by_chapter:
            articles_by_chapter[chapter] = []
        articles_by_chapter[chapter].append(article)

    # Sort chapters by start line
    sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

    xml_parts = ["    <body>"]

    for chapter in sorted_chapters:
        chapter_id = f"chp_{chapter.chapter_number}"

        xml_parts.extend([
            f'      <chapter id="{chapter_id}">',
            f'        <num>CHAPTER {chapter.chapter_number}</num>',
            f'        <heading>{chapter.title}</heading>'
        ])

        # Add articles for this chapter
        chapter_articles = articles_by_chapter.get(chapter.chapter_number, [])
        if chapter_articles:
            # Sort articles by article number
            sorted_articles = sorted(chapter_articles, key=lambda art: art.article_number)

            for article in sorted_articles:
                article_xml = build_article_xml(article)
                # Indent article XML properly within chapter
                indented_article = '\n'.join('        ' + line for line in article_xml.split('\n') if line.strip())
                xml_parts.append(indented_article)
        else:
            xml_parts.append('        <!-- No articles in this chapter -->')

        xml_parts.append('      </chapter>')

    xml_parts.append("    </body>")

    return '\n'.join(xml_parts)