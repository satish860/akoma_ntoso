import pytest
import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.pdf_extractor import extract_text
from src.transform.metadata_extractor import MetadataExtractor
from src.transform.frbr_builder import build_frbr_metadata

@pytest.mark.integration
def test_metadata_extraction_pipeline():
    """Full integration test: PDF → Extract → Validate → FRBR XML"""

    # Step 1: Extract text from DORA
    text = extract_text("data/dora/level1/DORA_Regulation_EU_2022_2554.pdf")
    assert len(text) > 0, "Should extract text from PDF"

    # Step 2: Extract metadata with LLM validation
    extractor = MetadataExtractor()
    metadata, validation = extractor.extract_with_validation(text)

    # Step 3: Check validation results
    print(f"Extraction confidence: {validation.confidence}%")
    print(f"Validation result: {'Valid' if validation.is_valid else 'Invalid'}")
    if validation.issues:
        print(f"Issues: {validation.issues}")

    assert validation.confidence > 70, f"Low confidence: {validation.confidence}%"

    # Step 4: Verify expected values for DORA
    assert metadata.document_type.lower() in ["regulation", "reg"], f"Unexpected type: {metadata.document_type}"
    assert metadata.number == "2022/2554", f"Unexpected number: {metadata.number}"
    assert "digital operational resilience" in metadata.title.lower(), f"Title doesn't match: {metadata.title}"
    assert metadata.date_enacted == date(2022, 12, 14), f"Unexpected date: {metadata.date_enacted}"
    assert metadata.country == "eu", f"Unexpected country: {metadata.country}"
    assert metadata.language == "eng", f"Unexpected language: {metadata.language}"

    # Step 5: Generate FRBR XML
    frbr_xml = build_frbr_metadata(metadata)
    assert "<FRBRWork>" in frbr_xml, "Should contain FRBRWork element"
    assert "2022-2554" in frbr_xml or "2022/2554" in frbr_xml, "Should contain document number"
    assert metadata.title in frbr_xml, "Should contain document title"

    # Output results
    print(f"[OK] Extracted metadata with {validation.confidence}% confidence")
    print(f"[OK] Document: {metadata.document_type} {metadata.number}")
    print(f"[OK] Title: {metadata.title[:50]}...")
    print(f"[OK] Generated valid FRBR XML")

    return metadata, frbr_xml

@pytest.mark.integration
def test_level2_document_extraction():
    """Test with Level 2 DORA document"""
    text = extract_text("data/dora/level2/pillar1_ict_risk/Commission_Delegated_Regulation_2024_1774_ICT_Risk_Management.pdf")
    assert len(text) > 0

    extractor = MetadataExtractor()
    metadata, validation = extractor.extract_with_validation(text)

    print(f"Level 2 document confidence: {validation.confidence}%")
    print(f"Document type: {metadata.document_type}")
    print(f"Number: {metadata.number}")

    assert validation.confidence > 60, f"Low confidence for Level 2: {validation.confidence}%"
    assert metadata.document_type.lower() in ["regulation", "delegated regulation"], f"Unexpected type: {metadata.document_type}"
    assert metadata.country == "eu"

    # Generate FRBR XML
    frbr_xml = build_frbr_metadata(metadata)
    assert "<meta>" in frbr_xml
    print(f"[OK] Level 2 document processed successfully")

if __name__ == "__main__":
    # Run tests manually (requires OPENROUTER_API_KEY)
    print("Testing DORA Level 1 document...")
    test_metadata_extraction_pipeline()

    print("\nTesting Level 2 document...")
    test_level2_document_extraction()

    print("\nAll integration tests passed!")