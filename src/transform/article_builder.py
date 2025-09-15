from typing import List, Dict
from .models import ArticleInfo, ChapterInfo

def build_chapters_with_articles_xml(chapters: List[ChapterInfo], articles: List[ArticleInfo]) -> str:
    """
    Build Akoma Ntoso XML structure for chapters containing articles.

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

    # Sort chapters by line number to ensure proper order
    sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

    xml_parts = ["    <body>"]

    for chapter in sorted_chapters:
        # Create chapter ID from Roman numeral (e.g., "chp_I", "chp_II")
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

        xml_parts.append('      </chapter>')

    xml_parts.append("    </body>")

    return '\n'.join(xml_parts)

def build_article_xml(article: ArticleInfo) -> str:
    """
    Build XML structure for a single article.

    Args:
        article: ArticleInfo object

    Returns:
        XML string for the article
    """
    article_id = f"art_{article.article_number}"

    xml_parts = [
        f'<article id="{article_id}">',
        f'  <num>{article.article_number}</num>',
        f'  <heading>{article.title}</heading>',
        '  <!-- Article content will be parsed and structured here -->',
        '</article>'
    ]

    return '\n'.join(xml_parts)

def build_article_with_content_xml(article: ArticleInfo, content: str) -> str:
    """
    Build XML structure for a single article with parsed content.

    Args:
        article: ArticleInfo object
        content: Full text content of the article

    Returns:
        XML string for the article with structured content
    """
    article_id = f"art_{article.article_number}"

    xml_parts = [
        f'<article id="{article_id}">',
        f'  <num>{article.article_number}</num>',
        f'  <heading>{article.title}</heading>'
    ]

    # Parse content into paragraphs, subparagraphs, etc.
    content_xml = parse_article_content(content, article.article_number)
    xml_parts.append(content_xml)

    xml_parts.append('</article>')

    return '\n'.join(xml_parts)

def parse_article_content(content: str, article_number: int) -> str:
    """
    Parse article content into structured paragraphs and subparagraphs.

    Args:
        content: Raw text content of the article
        article_number: Article number for generating IDs

    Returns:
        XML string with structured content
    """
    lines = content.strip().split('\n')
    xml_parts = []

    current_paragraph = None
    paragraph_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip the article header lines (already handled)
        if line.startswith(f'Article {article_number}') or line == article_number:
            continue

        # Check for paragraph markers (1., 2., 3., etc.)
        if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            # Close previous paragraph if exists
            if current_paragraph is not None:
                xml_parts.append('  </paragraph>')

            # Start new paragraph
            paragraph_count += 1
            paragraph_id = f"art_{article_number}_para_{paragraph_count}"

            # Extract paragraph number and content
            parts = line.split('.', 1)
            para_num = parts[0]
            para_content = parts[1].strip() if len(parts) > 1 else ""

            xml_parts.extend([
                f'  <paragraph id="{paragraph_id}">',
                f'    <num>{para_num}.</num>'
            ])

            if para_content:
                xml_parts.append(f'    <content>{para_content}</content>')

            current_paragraph = paragraph_count

        # Check for subparagraph markers (a), (b), (c), etc.
        elif line.startswith(('(a)', '(b)', '(c)', '(d)', '(e)', '(f)', '(g)', '(h)', '(i)', '(j)')):
            if current_paragraph is not None:
                # Extract subparagraph marker and content
                marker_end = line.find(')')
                if marker_end != -1:
                    marker = line[:marker_end + 1]
                    sub_content = line[marker_end + 1:].strip()

                    subpara_id = f"art_{article_number}_para_{current_paragraph}_subpara_{marker[1]}"

                    xml_parts.extend([
                        f'    <subparagraph id="{subpara_id}">',
                        f'      <num>{marker}</num>',
                        f'      <content>{sub_content}</content>',
                        '    </subparagraph>'
                    ])

        # Check for point markers (i), (ii), (iii), etc.
        elif line.startswith(('(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)')):
            if current_paragraph is not None:
                # Extract point marker and content
                marker_end = line.find(')')
                if marker_end != -1:
                    marker = line[:marker_end + 1]
                    point_content = line[marker_end + 1:].strip()

                    point_id = f"art_{article_number}_para_{current_paragraph}_point_{marker[1:-1]}"

                    xml_parts.extend([
                        f'    <point id="{point_id}">',
                        f'      <num>{marker}</num>',
                        f'      <content>{point_content}</content>',
                        '    </point>'
                    ])

        else:
            # Regular content line - add to current paragraph
            if current_paragraph is not None:
                xml_parts.append(f'    <content>{line}</content>')
            else:
                # Content before first paragraph - create implicit paragraph
                paragraph_count += 1
                paragraph_id = f"art_{article_number}_para_{paragraph_count}"
                xml_parts.extend([
                    f'  <paragraph id="{paragraph_id}">',
                    f'    <content>{line}</content>'
                ])
                current_paragraph = paragraph_count

    # Close last paragraph if exists
    if current_paragraph is not None:
        xml_parts.append('  </paragraph>')

    return '\n'.join(xml_parts)

def get_articles_summary(articles: List[ArticleInfo]) -> dict:
    """
    Get summary statistics about the articles.

    Args:
        articles: List of ArticleInfo objects

    Returns:
        Dictionary with summary statistics
    """
    if not articles:
        return {
            "count": 0,
            "chapters_with_articles": [],
            "articles_by_chapter": {},
            "first_article": None,
            "last_article": None,
            "confidence_avg": 0,
            "line_range": (0, 0)
        }

    # Group by chapter
    articles_by_chapter = {}
    for article in articles:
        chapter = article.parent_chapter
        if chapter not in articles_by_chapter:
            articles_by_chapter[chapter] = []
        articles_by_chapter[chapter].append(article)

    # Sort articles globally by line number
    sorted_articles = sorted(articles, key=lambda art: art.start_line)
    confidences = [art.confidence for art in articles]

    # Calculate chapter statistics
    chapter_stats = {}
    for chapter, chapter_articles in articles_by_chapter.items():
        sorted_chapter_articles = sorted(chapter_articles, key=lambda art: art.article_number)
        chapter_stats[chapter] = {
            "count": len(chapter_articles),
            "first_article": sorted_chapter_articles[0].article_number,
            "last_article": sorted_chapter_articles[-1].article_number,
            "article_numbers": [art.article_number for art in sorted_chapter_articles]
        }

    return {
        "count": len(articles),
        "chapters_with_articles": list(articles_by_chapter.keys()),
        "articles_by_chapter": chapter_stats,
        "first_article": sorted_articles[0].article_number,
        "last_article": sorted_articles[-1].article_number,
        "confidence_avg": sum(confidences) // len(confidences) if confidences else 0,
        "line_range": (sorted_articles[0].start_line, sorted_articles[-1].start_line)
    }

def validate_articles_xml(xml_content: str) -> dict:
    """
    Basic validation of generated articles XML.

    Args:
        xml_content: Generated XML string

    Returns:
        Dictionary with validation results
    """
    validation = {
        "has_body": "<body>" in xml_content,
        "has_chapters": "<chapter" in xml_content,
        "has_articles": "<article" in xml_content,
        "article_count": xml_content.count("<article"),
        "chapter_count": xml_content.count("<chapter"),
        "has_article_headings": xml_content.count("<heading>") >= xml_content.count("<article"),
        "has_article_nums": xml_content.count("<num>") >= xml_content.count("<article"),
        "is_well_formed": True  # Basic check
    }

    # Check if all articles have required elements
    article_count = validation["article_count"]
    article_heading_count = xml_content.count('</article>')  # Each article should be closed

    validation["all_articles_complete"] = (
        article_count == article_heading_count
    )

    return validation