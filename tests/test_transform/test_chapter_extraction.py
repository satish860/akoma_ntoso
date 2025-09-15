import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.transform.chapter_identifier import ChapterIdentifier

def test_chapter_extraction():
    """Test chapter extraction on DORA regulation"""
    print("=== Chapter Extraction Test ===\n")

    pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"

    # Test with first 20 pages using parallel processing
    print("1. Testing parallel chapter extraction on first 20 pages...")
    try:
        identifier = ChapterIdentifier()

        # Extract chapters from first 20 pages in parallel
        chapters = identifier.extract_all_chapters_parallel(pdf_path, start_page=1, end_page=20, max_workers=3)

        if chapters:
            print(f"\n2. Found {len(chapters)} chapters:")
            print("   " + "="*70)
            for i, chapter in enumerate(chapters, 1):
                print(f"   {i}. CHAPTER {chapter.chapter_number}")
                print(f"      Title: {chapter.title}")
                print(f"      Line: {chapter.start_line} (Page {chapter.page_number})")
                print(f"      Confidence: {chapter.confidence}%")
                print()

            # Validate sequence
            print("3. Validating chapter sequence...")
            validation = identifier.validate_chapter_sequence(chapters)

            print(f"   Total chapters: {validation['total_chapters']}")
            print(f"   Found sequence: {', '.join(validation['chapter_numbers'])}")
            print(f"   Expected sequence: {', '.join(validation['expected_sequence'])}")
            print(f"   Is sequential: {'✓' if validation['is_sequential'] else '✗'}")

            if validation['missing_chapters']:
                print(f"   Missing: {', '.join(validation['missing_chapters'])}")
            if validation['unexpected_chapters']:
                print(f"   Unexpected: {', '.join(validation['unexpected_chapters'])}")

            print("\n[OK] Chapter extraction test completed!")
            return chapters

        else:
            print("   No chapters found in first 50 pages")
            print("   This might indicate chapters start later in the document")

            # Try pages 21-40 in parallel
            print("\n2. Testing pages 21-40 in parallel...")
            chapters = identifier.extract_all_chapters_parallel(pdf_path, start_page=21, end_page=40, max_workers=3)

            if chapters:
                print(f"   Found {len(chapters)} chapters in pages 21-40")
                for chapter in chapters:
                    print(f"   CHAPTER {chapter.chapter_number}: {chapter.title}")
            else:
                print("   No chapters found in pages 21-40 either")

            return chapters

    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure OPENROUTER_API_KEY is set in .env file")
        return None

def test_single_page():
    """Test chapter identification on a specific page"""
    print("\n=== Single Page Test ===")

    # Test page iterator
    from src.transform.page_iterator import iterate_pages_with_lines

    pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"

    print("Testing page iterator on first 3 pages...")
    page_count = 0
    for page_num, page_text, line_offset in iterate_pages_with_lines(pdf_path):
        page_count += 1
        print(f"Page {page_num}: {len(page_text)} characters, starts at line {line_offset}")

        if page_count >= 3:
            break

    print("[OK] Page iterator test completed!")

if __name__ == "__main__":
    test_single_page()
    test_chapter_extraction()