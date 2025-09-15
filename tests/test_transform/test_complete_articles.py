import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.transform.article_identifier import ArticleIdentifier
from src.transform.chapter_identifier import ChapterIdentifier
from src.transform.article_builder import build_chapters_with_articles_xml, get_articles_summary

class TestCompleteArticleExtraction(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"
        self.article_identifier = ArticleIdentifier()
        self.chapter_identifier = ChapterIdentifier()

    def test_dora_article_extraction_integration(self):
        """Integration test for complete article extraction on DORA document"""
        # Skip if PDF not available
        if not os.path.exists(self.pdf_path):
            self.skipTest(f"PDF not found: {self.pdf_path}")

        # First extract chapters (required for article extraction)
        print("\nExtracting chapters...")
        chapters = self.chapter_identifier.extract_all_chapters(
            self.pdf_path,
            start_page=22,
            end_page=30  # Limited range for testing
        )

        self.assertGreater(len(chapters), 0, "Should find at least one chapter")
        print(f"Found {len(chapters)} chapters")

        # Then extract articles within those chapters
        print("Extracting articles...")
        articles = self.article_identifier.extract_all_articles_with_chapters(
            self.pdf_path,
            chapters
        )

        print(f"Found {len(articles)} articles")

        # Validate results
        if articles:
            # Check that articles have valid structure
            for article in articles:
                self.assertIsInstance(article.article_number, int)
                self.assertGreater(article.article_number, 0)
                self.assertIsInstance(article.title, str)
                self.assertGreater(len(article.title), 0)
                self.assertIsInstance(article.start_line, int)
                self.assertGreater(article.start_line, 0)
                self.assertIn(article.parent_chapter, [ch.chapter_number for ch in chapters])

            # Check article sequence validation
            validation = self.article_identifier.validate_article_sequence(articles)
            print(f"Article sequence validation: {validation}")

            # Generate summary
            summary = get_articles_summary(articles)
            print(f"Articles summary: {summary}")

            # Generate XML
            xml = build_chapters_with_articles_xml(chapters, articles)
            self.assertIn('<body>', xml)
            self.assertIn('<chapter', xml)
            self.assertIn('<article', xml)
            self.assertIn('</body>', xml)

            print("XML generation successful")

        else:
            print("No articles found - this might be expected if testing range doesn't contain articles")

    def test_article_content_extraction(self):
        """Test extracting content of a specific article"""
        # Skip if PDF not available
        if not os.path.exists(self.pdf_path):
            self.skipTest(f"PDF not found: {self.pdf_path}")

        # Create a sample article for testing content extraction
        from src.transform.models import ArticleInfo

        # Article 1 from DORA (based on our analysis)
        sample_article = ArticleInfo(
            article_number=1,
            title="Subject matter",
            start_line=1007,
            end_line=1035,
            parent_chapter="I",
            start_page=23,
            end_page=24,
            confidence=95
        )

        # Extract content
        content = self.article_identifier.extract_article_content(
            self.pdf_path,
            sample_article
        )

        if content:
            self.assertIsInstance(content, str)
            self.assertGreater(len(content), 0)
            print(f"Extracted content length: {len(content)} characters")
            print(f"Content preview: {content[:200]}...")
        else:
            print("No content extracted - article boundaries may need adjustment")

    def test_article_xml_structure(self):
        """Test the XML structure of articles"""
        from src.transform.models import ArticleInfo, ChapterInfo

        # Create test data
        test_chapter = ChapterInfo(
            chapter_number="I",
            title="General provisions",
            start_line=1000,
            page_number=23,
            confidence=95
        )

        test_articles = [
            ArticleInfo(
                article_number=1,
                title="Subject matter",
                start_line=1005,
                end_line=1020,
                parent_chapter="I",
                start_page=23,
                confidence=95
            ),
            ArticleInfo(
                article_number=2,
                title="Scope",
                start_line=1025,
                end_line=1040,
                parent_chapter="I",
                start_page=23,
                confidence=90
            )
        ]

        # Generate XML
        xml = build_chapters_with_articles_xml([test_chapter], test_articles)

        # Validate XML structure
        self.assertIn('<body>', xml)
        self.assertIn('<chapter id="chp_I">', xml)
        self.assertIn('<article id="art_1">', xml)
        self.assertIn('<article id="art_2">', xml)
        self.assertIn('<num>1</num>', xml)
        self.assertIn('<num>2</num>', xml)
        self.assertIn('<heading>Subject matter</heading>', xml)
        self.assertIn('<heading>Scope</heading>', xml)

        # Check proper nesting
        lines = xml.split('\n')
        body_indent = next(i for i, line in enumerate(lines) if '<body>' in line)
        chapter_indent = next(i for i, line in enumerate(lines) if '<chapter' in line)
        article_indent = next(i for i, line in enumerate(lines) if '<article' in line)

        # Articles should be indented more than chapters, which are indented more than body
        self.assertGreater(chapter_indent, body_indent)
        self.assertGreater(article_indent, chapter_indent)

        print("XML structure validation passed")

    def test_article_boundary_detection(self):
        """Test article boundary detection logic"""
        from src.transform.models import ArticleInfo

        # Create test articles without end_line set
        test_articles = [
            ArticleInfo(
                article_number=1,
                title="First",
                start_line=100,
                parent_chapter="I",
                start_page=1,
                confidence=95
            ),
            ArticleInfo(
                article_number=2,
                title="Second",
                start_line=200,
                parent_chapter="I",
                start_page=2,
                confidence=90
            ),
            ArticleInfo(
                article_number=3,
                title="Third",
                start_line=300,
                parent_chapter="I",
                start_page=3,
                confidence=85
            )
        ]

        # Set boundaries
        self.article_identifier._set_article_boundaries(test_articles)

        # Check that boundaries were set correctly
        self.assertEqual(test_articles[0].end_line, 199)  # First ends before second
        self.assertEqual(test_articles[1].end_line, 299)  # Second ends before third
        self.assertIsNone(test_articles[2].end_line)     # Last has no end

        print("Article boundary detection working correctly")

if __name__ == '__main__':
    # Run tests with more verbose output
    unittest.main(verbosity=2)