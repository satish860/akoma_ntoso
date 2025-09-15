import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.transform.article_identifier import ArticleIdentifier
from src.transform.article_builder import build_chapters_with_articles_xml, get_articles_summary, build_article_xml
from src.transform.models import ArticleInfo, ChapterInfo

class TestArticleExtraction(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.identifier = ArticleIdentifier()

        # Sample chapters for testing
        self.sample_chapters = [
            ChapterInfo(
                chapter_number="I",
                title="General provisions",
                start_line=1005,
                page_number=23,
                confidence=95
            ),
            ChapterInfo(
                chapter_number="II",
                title="ICT risk management",
                start_line=1200,
                page_number=25,
                confidence=90
            )
        ]

        # Sample articles for testing
        self.sample_articles = [
            ArticleInfo(
                article_number=1,
                title="Subject matter",
                start_line=1007,
                end_line=1035,
                parent_chapter="I",
                start_page=23,
                end_page=24,
                confidence=95
            ),
            ArticleInfo(
                article_number=2,
                title="Scope",
                start_line=1037,
                end_line=1076,
                parent_chapter="I",
                start_page=24,
                end_page=25,
                confidence=92
            ),
            ArticleInfo(
                article_number=3,
                title="Definitions",
                start_line=1079,
                end_line=1199,
                parent_chapter="I",
                start_page=25,
                end_page=26,
                confidence=88
            )
        ]

    def test_article_info_model(self):
        """Test ArticleInfo model creation and validation"""
        article = ArticleInfo(
            article_number=1,
            title="Test Article",
            start_line=100,
            end_line=150,
            parent_chapter="I",
            start_page=5,
            end_page=6,
            confidence=95
        )

        self.assertEqual(article.article_number, 1)
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.start_line, 100)
        self.assertEqual(article.end_line, 150)
        self.assertEqual(article.parent_chapter, "I")
        self.assertEqual(article.start_page, 5)
        self.assertEqual(article.end_page, 6)
        self.assertEqual(article.confidence, 95)

    def test_article_boundaries(self):
        """Test setting article boundaries"""
        articles = [
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
            )
        ]

        self.identifier._set_article_boundaries(articles)

        # First article should end where second starts
        self.assertEqual(articles[0].end_line, 199)
        # Last article should have no end_line
        self.assertIsNone(articles[1].end_line)

    def test_get_articles_summary(self):
        """Test articles summary generation"""
        summary = get_articles_summary(self.sample_articles)

        self.assertEqual(summary['count'], 3)
        self.assertEqual(summary['first_article'], 1)
        self.assertEqual(summary['last_article'], 3)
        self.assertEqual(summary['chapters_with_articles'], ['I'])
        self.assertIn('I', summary['articles_by_chapter'])
        self.assertEqual(summary['articles_by_chapter']['I']['count'], 3)
        self.assertEqual(summary['articles_by_chapter']['I']['first_article'], 1)
        self.assertEqual(summary['articles_by_chapter']['I']['last_article'], 3)

    def test_build_article_xml(self):
        """Test individual article XML generation"""
        article = self.sample_articles[0]
        xml = build_article_xml(article)

        self.assertIn('<article id="art_1">', xml)
        self.assertIn('<num>1</num>', xml)
        self.assertIn('<heading>Subject matter</heading>', xml)
        self.assertIn('</article>', xml)

    def test_build_chapters_with_articles_xml(self):
        """Test complete chapters with articles XML generation"""
        xml = build_chapters_with_articles_xml(self.sample_chapters, self.sample_articles)

        # Check for body structure
        self.assertIn('<body>', xml)
        self.assertIn('</body>', xml)

        # Check for chapter structure
        self.assertIn('<chapter id="chp_I">', xml)
        self.assertIn('<num>CHAPTER I</num>', xml)
        self.assertIn('<heading>General provisions</heading>', xml)

        # Check for articles within chapter
        self.assertIn('<article id="art_1">', xml)
        self.assertIn('<article id="art_2">', xml)
        self.assertIn('<article id="art_3">', xml)

        # Check hierarchy (articles nested in chapters)
        chapter_pos = xml.find('<chapter id="chp_I">')
        article_pos = xml.find('<article id="art_1">')
        chapter_end_pos = xml.find('</chapter>')

        self.assertTrue(chapter_pos < article_pos < chapter_end_pos)

    def test_empty_articles_summary(self):
        """Test summary with empty articles list"""
        summary = get_articles_summary([])

        self.assertEqual(summary['count'], 0)
        self.assertIsNone(summary['first_article'])
        self.assertIsNone(summary['last_article'])
        self.assertEqual(summary['chapters_with_articles'], [])
        self.assertEqual(summary['articles_by_chapter'], {})
        self.assertEqual(summary['confidence_avg'], 0)

    def test_empty_chapters_xml(self):
        """Test XML generation with empty chapters list"""
        xml = build_chapters_with_articles_xml([], [])

        self.assertIn('<body>', xml)
        self.assertIn('<!-- No chapters found -->', xml)
        self.assertIn('</body>', xml)

    def test_validate_article_sequence(self):
        """Test article sequence validation"""
        validation = self.identifier.validate_article_sequence(self.sample_articles)

        self.assertIn('I', validation)
        chapter_validation = validation['I']

        self.assertEqual(chapter_validation['total_articles'], 3)
        self.assertEqual(chapter_validation['article_numbers'], [1, 2, 3])
        self.assertEqual(chapter_validation['expected_sequence'], [1, 2, 3])
        self.assertTrue(chapter_validation['is_sequential'])
        self.assertEqual(chapter_validation['missing_articles'], [])
        self.assertEqual(chapter_validation['unexpected_articles'], [])

    def test_validate_broken_sequence(self):
        """Test validation with broken article sequence"""
        broken_articles = [
            ArticleInfo(
                article_number=1,
                title="First",
                start_line=100,
                parent_chapter="I",
                start_page=1,
                confidence=95
            ),
            ArticleInfo(
                article_number=3,  # Missing article 2
                title="Third",
                start_line=200,
                parent_chapter="I",
                start_page=2,
                confidence=90
            )
        ]

        validation = self.identifier.validate_article_sequence(broken_articles)

        self.assertIn('I', validation)
        chapter_validation = validation['I']

        self.assertEqual(chapter_validation['total_articles'], 2)
        self.assertEqual(chapter_validation['article_numbers'], [1, 3])
        self.assertEqual(chapter_validation['expected_sequence'], [1, 2])
        self.assertFalse(chapter_validation['is_sequential'])
        self.assertEqual(chapter_validation['missing_articles'], [2])
        self.assertEqual(chapter_validation['unexpected_articles'], [3])

    def test_multiple_chapters_with_articles(self):
        """Test articles across multiple chapters"""
        multi_chapter_articles = self.sample_articles + [
            ArticleInfo(
                article_number=4,
                title="ICT Strategy",
                start_line=1205,
                parent_chapter="II",
                start_page=25,
                confidence=85
            )
        ]

        summary = get_articles_summary(multi_chapter_articles)

        self.assertEqual(summary['count'], 4)
        self.assertEqual(len(summary['chapters_with_articles']), 2)
        self.assertIn('I', summary['chapters_with_articles'])
        self.assertIn('II', summary['chapters_with_articles'])
        self.assertEqual(summary['articles_by_chapter']['I']['count'], 3)
        self.assertEqual(summary['articles_by_chapter']['II']['count'], 1)

if __name__ == '__main__':
    unittest.main()