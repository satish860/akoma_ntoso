import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.pdf_extractor import extract_text_with_line_numbers, extract_lines_range
from src.transform.recitals_identifier import RecitalsIdentifier
from src.transform.recitals_builder import build_recitals_xml, get_recitals_summary, parse_recitals_text

def test_recitals_extraction():
    """Test recitals extraction on DORA regulation"""
    print("=== Recitals Extraction Test ===\n")

    # Step 1: Extract text with line numbers
    print("1. Extracting text with line numbers...")
    pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"
    numbered_text, line_mapping = extract_text_with_line_numbers(pdf_path)

    print(f"   Extracted {len(numbered_text.split())} lines with numbers")
    print()

    # Step 2: Identify recitals location
    print("2. Identifying recitals with LLM...")
    try:
        identifier = RecitalsIdentifier()
        recitals_location = identifier.identify_recitals(numbered_text)

        print(f"   Recitals found:")
        print(f"   - Start line (Whereas:): {recitals_location.start_line}")
        print(f"   - End line: {recitals_location.end_line}")
        print(f"   - First recital line: {recitals_location.first_recital_line}")
        print(f"   - Total recitals: {recitals_location.recital_count}")
        print(f"   - Last recital number: ({recitals_location.last_recital_number})")
        print(f"   - Confidence: {recitals_location.confidence}%")
        print()

        # Step 3: Extract exact recitals text
        print("3. Extracting exact recitals text...")
        recitals_text = extract_lines_range(
            pdf_path,
            recitals_location.start_line,
            recitals_location.end_line
        )

        print(f"   Extracted recitals ({len(recitals_text)} characters)")
        print("   Sample first 300 characters:")
        print("   " + "="*60)
        print(recitals_text[:300] + "...")
        print("   " + "="*60)
        print()

        # Step 4: Parse individual recitals
        print("4. Parsing individual recitals...")
        recitals = parse_recitals_text(recitals_text)
        summary = get_recitals_summary(recitals_text)

        print(f"   Parsed {summary['count']} recitals")
        print(f"   Numbers: ({summary['first_number']}) to ({summary['last_number']})")
        print(f"   Average length: {summary['average_length']} characters")
        print()

        # Show first few recitals
        print("   First 3 recitals:")
        for i, (num, content) in enumerate(recitals[:3]):
            print(f"   ({num}) {content[:100]}...")
        print()

        # Step 5: Generate XML
        print("5. Generating Akoma Ntoso XML...")
        recitals_xml = build_recitals_xml(recitals_text)

        print(f"   Generated XML ({len(recitals_xml)} characters)")
        print("   Sample XML structure:")
        print("   " + "="*60)
        # Show first 800 characters of XML
        xml_lines = recitals_xml.split('\n')[:20]
        print('\n'.join(xml_lines))
        print("   ...")
        print("   " + "="*60)
        print()

        print("[OK] Recitals extraction test completed successfully!")

        return recitals_location, recitals_text, recitals_xml

    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure OPENROUTER_API_KEY is set in .env file")
        return None, None, None

if __name__ == "__main__":
    test_recitals_extraction()