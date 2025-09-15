import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.transform.chapter_identifier import ChapterIdentifier
from src.transform.chapter_builder import build_chapters_xml, get_chapters_summary, validate_chapter_xml

def test_complete_chapter_extraction():
    """Test complete chapter extraction and XML generation"""
    print("=== Complete Chapter Extraction Test ===\n")

    pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"

    # Extract all chapters from DORA (scan pages 20-80 to find all chapters)
    print("1. Extracting all chapters from DORA (pages 20-80)...")
    try:
        identifier = ChapterIdentifier()

        # Use parallel extraction for speed
        chapters = identifier.extract_all_chapters_parallel(
            pdf_path,
            start_page=20,
            end_page=80,
            max_workers=4
        )

        if chapters:
            print(f"\n2. Chapter extraction results:")
            print("   " + "="*70)

            # Get summary
            summary = get_chapters_summary(chapters)
            print(f"   Total chapters: {summary['count']}")
            print(f"   Chapter range: {summary['first_chapter']} to {summary['last_chapter']}")
            print(f"   Pages span: {summary['pages_span']} pages")
            print(f"   Line range: {summary['line_range'][0]} to {summary['line_range'][1]}")
            print(f"   Sequence: {' → '.join(summary['chapter_sequence'])}")
            print(f"   Avg confidence: {summary['confidence_avg']}%")
            print()

            # Show individual chapters
            print("   Individual chapters:")
            for i, chapter in enumerate(sorted(chapters, key=lambda ch: ch.start_line), 1):
                print(f"   {i}. CHAPTER {chapter.chapter_number}")
                print(f"      Title: {chapter.title}")
                print(f"      Line: {chapter.start_line} (Page {chapter.page_number})")
                print()

            # Generate XML
            print("3. Generating Akoma Ntoso XML...")
            chapters_xml = build_chapters_xml(chapters)

            print(f"   Generated XML ({len(chapters_xml)} characters)")
            print("   Sample XML structure:")
            print("   " + "="*60)

            # Show first 20 lines of XML
            xml_lines = chapters_xml.split('\n')[:20]
            for line in xml_lines:
                print(f"   {line}")
            if len(xml_lines) > 20:
                print("   ...")
            print("   " + "="*60)
            print()

            # Validate XML
            print("4. Validating XML structure...")
            validation = validate_chapter_xml(chapters_xml)

            print(f"   Has body: {'✓' if validation['has_body'] else '✗'}")
            print(f"   Has chapters: {'✓' if validation['has_chapters'] else '✗'}")
            print(f"   Chapter count: {validation['chapter_count']}")
            print(f"   All complete: {'✓' if validation['all_chapters_complete'] else '✗'}")
            print()

            # Validate sequence
            print("5. Validating chapter sequence...")
            sequence_validation = identifier.validate_chapter_sequence(chapters)

            print(f"   Is sequential: {'✓' if sequence_validation['is_sequential'] else '✗'}")
            if sequence_validation['missing_chapters']:
                print(f"   Missing: {', '.join(sequence_validation['missing_chapters'])}")
            if sequence_validation['unexpected_chapters']:
                print(f"   Unexpected: {', '.join(sequence_validation['unexpected_chapters'])}")

            print("\n[OK] Complete chapter extraction test completed!")
            return chapters, chapters_xml

        else:
            print("   No chapters found in pages 20-80")
            return None, None

    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure OPENROUTER_API_KEY is set in .env file")
        return None, None

if __name__ == "__main__":
    test_complete_chapter_extraction()