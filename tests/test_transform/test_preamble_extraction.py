import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.pdf_extractor import extract_text_with_line_numbers, extract_lines_range
from src.transform.preamble_identifier import PreambleIdentifier

def test_preamble_extraction():
    """Test preamble extraction on DORA regulation"""
    print("=== Preamble Extraction Test ===\n")

    # Step 1: Extract text with line numbers
    print("1. Extracting text with line numbers...")
    pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"
    numbered_text, line_mapping = extract_text_with_line_numbers(pdf_path)

    print(f"   Extracted {len(numbered_text.split())} lines with numbers")
    print(f"   Sample first 5 lines:")
    for line in numbered_text.split('\n')[:5]:
        print(f"   {line}")
    print()

    # Step 2: Identify preamble location
    print("2. Identifying preamble with LLM...")
    try:
        identifier = PreambleIdentifier()
        preamble_location = identifier.identify_preamble(numbered_text)

        print(f"   Preamble found:")
        print(f"   - Start line: {preamble_location.start_line}")
        print(f"   - End line: {preamble_location.end_line}")
        print(f"   - Title: {preamble_location.title}")
        print(f"   - Date: {preamble_location.date}")
        print(f"   - Legal basis statements: {len(preamble_location.legal_basis)}")
        print(f"   - Confidence: {preamble_location.confidence}%")
        print()

        # Step 3: Extract exact preamble text
        print("3. Extracting exact preamble text...")
        preamble_text = extract_lines_range(
            pdf_path,
            preamble_location.start_line,
            preamble_location.end_line
        )

        print(f"   Extracted preamble ({len(preamble_text)} characters):")
        print("   " + "="*60)
        print(preamble_text[:500] + "..." if len(preamble_text) > 500 else preamble_text)
        print("   " + "="*60)
        print()

        # Step 4: Show legal basis statements
        print("4. Legal basis statements found:")
        for i, statement in enumerate(preamble_location.legal_basis, 1):
            print(f"   {i}. {statement[:80]}...")
        print()

        print("[OK] Preamble extraction test completed successfully!")

        return preamble_location, preamble_text

    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure OPENROUTER_API_KEY is set in .env file")
        return None, None

if __name__ == "__main__":
    test_preamble_extraction()