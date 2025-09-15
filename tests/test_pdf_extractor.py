import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.pdf_extractor import extract_text

def test_extract_text():
    """Test extracting text from DORA regulation PDF"""
    # Test with main DORA regulation
    pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"
    text = extract_text(pdf_path)

    # Basic assertions
    assert len(text) > 0, "Should extract some text"
    assert "REGULATION" in text, "Should contain 'REGULATION'"
    assert "digital operational resilience" in text, "Should contain document title"

    print(f"Extracted {len(text)} characters from DORA regulation")
    print(f"First 200 characters: {text[:200]}")

def test_extract_text_level2():
    """Test extracting text from Level 2 documents"""
    pdf_path = "data/dora/level2/pillar1_ict_risk/Commission_Delegated_Regulation_2024_1774_ICT_Risk_Management.pdf"
    text = extract_text(pdf_path)

    assert len(text) > 0, "Should extract some text from Level 2 document"
    print(f"Extracted {len(text)} characters from Level 2 document")

if __name__ == "__main__":
    test_extract_text()
    test_extract_text_level2()
    print("All tests passed!")