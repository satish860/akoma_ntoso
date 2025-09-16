import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.transform.article_content_extractor import ArticleContentExtractor
from src.transform.article_builder import build_article_with_full_content_xml, get_content_summary
from src.transform.models import ArticleInfo, ArticleContent, ParagraphContent, SubparagraphContent, PointContent

class TestContentExtraction(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = ArticleContentExtractor(use_llm_fallback=False)  # Test regex only

        # Sample article for testing
        self.sample_article = ArticleInfo(
            article_number=1,
            title="Subject matter",
            start_line=1007,
            end_line=1035,
            parent_chapter="I",
            start_page=23,
            end_page=24,
            confidence=95
        )

        # Sample raw content for testing regex patterns
        self.sample_content = """Article 1
Subject matter
1. In order to achieve a high common level of digital operational resilience, this Regulation lays down uniform requirements concerning the security of network and information systems supporting the business processes of financial entities as follows:
(a) requirements applicable to financial entities in relation to:
(i) information and communication technology (ICT) risk management;
(ii) reporting of major ICT-related incidents and notifying, on a voluntary basis, significant cyber threats to the competent authorities;
(iii) reporting of major operational or security payment-related incidents to the competent authorities by financial entities referred to in Article 2(1), points (a) to (d);
(iv) digital operational resilience testing;
(v) information and intelligence sharing in relation to cyber threats and vulnerabilities;
(vi) measures for the sound management of ICT third-party risk;
(b) requirements in relation to the contractual arrangements concluded between ICT third-party service providers and financial entities;
(c) rules for the establishment and conduct of the Oversight Framework for critical ICT third-party service providers when providing services to financial entities;
(d) rules on cooperation among competent authorities, and rules on supervision and enforcement by competent authorities in relation to all matters covered by this Regulation.
2. In relation to financial entities identified as essential or important entities pursuant to national rules transposing Article 3 of Directive (EU) 2022/2555, this Regulation shall be considered a sector-specific Union legal act for the purposes of Article 4 of that Directive.
3. This Regulation is without prejudice to the responsibility of Member States regarding essential State functions concerning public security, defence and national security in accordance with Union law."""

    def test_regex_patterns(self):
        """Test individual regex patterns"""
        # Test paragraph pattern
        para_match = self.extractor.PARAGRAPH_PATTERN.match("1. This is a paragraph")
        self.assertIsNotNone(para_match)
        self.assertEqual(para_match.group(1), "1")
        self.assertEqual(para_match.group(2), "This is a paragraph")

        # Test subparagraph pattern
        subpara_match = self.extractor.SUBPARA_PATTERN.match("(a) This is a subparagraph")
        self.assertIsNotNone(subpara_match)
        self.assertEqual(subpara_match.group(1), "a")
        self.assertEqual(subpara_match.group(2), "This is a subparagraph")

        # Test point pattern
        point_match = self.extractor.POINT_PATTERN.match("(i) This is a point")
        self.assertIsNotNone(point_match)
        self.assertEqual(point_match.group(1), "i")
        self.assertEqual(point_match.group(2), "This is a point")

    def test_parse_content_with_regex(self):
        """Test parsing content with regex patterns"""
        paragraphs = self.extractor.parse_content_with_regex(self.sample_content, 1)

        # Should find 3 paragraphs
        self.assertEqual(len(paragraphs), 3)

        # Check first paragraph
        first_para = paragraphs[0]
        self.assertEqual(first_para.num, "1")
        self.assertTrue(len(first_para.content) > 0)
        self.assertEqual(len(first_para.subparagraphs), 4)  # (a), (b), (c), (d)

        # Check subparagraphs of first paragraph
        subpara_a = first_para.subparagraphs[0]
        self.assertEqual(subpara_a.marker, "(a)")
        self.assertEqual(len(subpara_a.points), 6)  # (i) through (vi)

        # Check points in first subparagraph
        point_i = subpara_a.points[0]
        self.assertEqual(point_i.marker, "(i)")
        self.assertIn("ICT risk management", point_i.content[0])

        # Check second paragraph
        second_para = paragraphs[1]
        self.assertEqual(second_para.num, "2")
        self.assertEqual(len(second_para.subparagraphs), 0)  # No subparagraphs

        # Check third paragraph
        third_para = paragraphs[2]
        self.assertEqual(third_para.num, "3")
        self.assertEqual(len(third_para.subparagraphs), 0)  # No subparagraphs

    def test_content_models(self):
        """Test content model creation and validation"""
        # Test PointContent
        point = PointContent(
            marker="(i)",
            content=["ICT risk management"]
        )
        self.assertEqual(point.marker, "(i)")
        self.assertEqual(len(point.content), 1)

        # Test SubparagraphContent
        subpara = SubparagraphContent(
            marker="(a)",
            content=["requirements applicable to financial entities"],
            points=[point]
        )
        self.assertEqual(subpara.marker, "(a)")
        self.assertEqual(len(subpara.points), 1)

        # Test ParagraphContent
        paragraph = ParagraphContent(
            num="1",
            content=["Main paragraph content"],
            subparagraphs=[subpara]
        )
        self.assertEqual(paragraph.num, "1")
        self.assertEqual(len(paragraph.subparagraphs), 1)

        # Test ArticleContent
        article_content = ArticleContent(
            article_number=1,
            title="Subject matter",
            paragraphs=[paragraph],
            extraction_method="regex"
        )
        self.assertEqual(article_content.article_number, 1)
        self.assertEqual(article_content.extraction_method, "regex")
        self.assertEqual(len(article_content.paragraphs), 1)

    def test_build_article_with_full_content_xml(self):
        """Test XML generation with full content"""
        # Parse sample content
        paragraphs = self.extractor.parse_content_with_regex(self.sample_content, 1)

        # Create ArticleContent
        content = ArticleContent(
            article_number=1,
            title="Subject matter",
            paragraphs=paragraphs,
            extraction_method="regex"
        )

        # Generate XML
        xml = build_article_with_full_content_xml(self.sample_article, content)

        # Validate XML structure
        self.assertIn('<article id="art_1">', xml)
        self.assertIn('<num>1</num>', xml)
        self.assertIn('<heading>Subject matter</heading>', xml)
        self.assertIn('<paragraph id="art_1_para_1">', xml)
        self.assertIn('<subparagraph id="art_1_para_1_subpara_a">', xml)
        self.assertIn('<point id="art_1_para_1_subpara_a_point_i">', xml)
        self.assertIn('</article>', xml)

        # Check content is present
        self.assertIn('ICT risk management', xml)
        self.assertIn('digital operational resilience', xml)

    def test_get_content_summary(self):
        """Test content summary generation"""
        # Parse sample content
        paragraphs = self.extractor.parse_content_with_regex(self.sample_content, 1)

        # Create multiple ArticleContent instances
        contents = {
            1: ArticleContent(
                article_number=1,
                title="Subject matter",
                paragraphs=paragraphs,
                extraction_method="regex"
            ),
            2: ArticleContent(
                article_number=2,
                title="Scope",
                paragraphs=[],
                extraction_method="failed"
            )
        }

        # Generate summary
        summary = get_content_summary(contents)

        self.assertEqual(summary['total_articles'], 2)
        self.assertEqual(summary['extraction_methods']['regex'], 1)
        self.assertEqual(summary['extraction_methods']['failed'], 1)
        self.assertGreater(summary['total_paragraphs'], 0)
        self.assertGreater(summary['total_subparagraphs'], 0)
        self.assertGreater(summary['total_points'], 0)
        self.assertEqual(summary['successful_extractions'], 1)
        self.assertEqual(summary['success_rate'], 50.0)

    def test_validate_content_structure(self):
        """Test content structure validation"""
        # Parse sample content
        paragraphs = self.extractor.parse_content_with_regex(self.sample_content, 1)

        content = ArticleContent(
            article_number=1,
            title="Subject matter",
            paragraphs=paragraphs,
            extraction_method="regex"
        )

        # Validate structure
        validation = self.extractor.validate_content_structure(content)

        self.assertEqual(validation['article_number'], 1)
        self.assertEqual(validation['extraction_method'], "regex")
        self.assertEqual(validation['total_paragraphs'], 3)
        self.assertGreater(validation['total_subparagraphs'], 0)
        self.assertGreater(validation['total_points'], 0)
        self.assertTrue(validation['is_sequential'])
        self.assertTrue(validation['has_content'])

    def test_empty_content_handling(self):
        """Test handling of empty or malformed content"""
        # Test empty content
        empty_paragraphs = self.extractor.parse_content_with_regex("", 1)
        self.assertEqual(len(empty_paragraphs), 0)

        # Test content with no structure
        simple_content = "Just some plain text without any structure"
        simple_paragraphs = self.extractor.parse_content_with_regex(simple_content, 1)
        self.assertEqual(len(simple_paragraphs), 1)  # Should create implicit paragraph
        self.assertEqual(simple_paragraphs[0].num, "1")

    def test_complex_numbering_patterns(self):
        """Test complex numbering patterns"""
        complex_content = """1. First paragraph
(a) First subparagraph
(i) First point
(ii) Second point
(iii) Third point
(b) Second subparagraph
(c) Third subparagraph
2. Second paragraph
3. Third paragraph"""

        paragraphs = self.extractor.parse_content_with_regex(complex_content, 1)

        self.assertEqual(len(paragraphs), 3)
        self.assertEqual(len(paragraphs[0].subparagraphs), 3)
        self.assertEqual(len(paragraphs[0].subparagraphs[0].points), 3)

        # Check sequential numbering
        para_nums = [p.num for p in paragraphs]
        self.assertEqual(para_nums, ["1", "2", "3"])

    def test_xml_escaping(self):
        """Test XML character escaping"""
        from src.transform.article_builder import escape_xml

        # Test basic escaping
        self.assertEqual(escape_xml("test & example"), "test &amp; example")
        self.assertEqual(escape_xml("test < example"), "test &lt; example")
        self.assertEqual(escape_xml("test > example"), "test &gt; example")
        self.assertEqual(escape_xml('test "quoted"'), "test &quot;quoted&quot;")

        # Test empty string
        self.assertEqual(escape_xml(""), "")
        self.assertEqual(escape_xml(None), "")

if __name__ == '__main__':
    unittest.main(verbosity=2)