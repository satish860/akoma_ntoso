import sys
import os
sys.path.append('.')

from src.pdf_extractor import extract_text, extract_text_with_line_numbers, extract_lines_range
from src.transform.metadata_extractor import MetadataExtractor
from src.transform.preamble_identifier import PreambleIdentifier
from src.transform.recitals_identifier import RecitalsIdentifier
from src.transform.recitals_builder import build_recitals_xml, get_recitals_summary
from src.transform.frbr_builder import build_frbr_metadata
from src.transform.akn_builder import create_akoma_ntoso_root

def main():
    print("=== Akoma Ntoso ETL Pipeline Demo ===\n")

    # Step 1: Extract (E in ETL)
    print("1. EXTRACT: Reading PDF text...")
    pdf_path = "data/dora/level1/DORA_Regulation_EU_2022_2554.pdf"
    text = extract_text(pdf_path)
    print(f"   Extracted {len(text):,} characters from DORA regulation")
    print(f"   Sample: {text[:150]}...\n")

    # Step 2: Transform (T in ETL) - Metadata
    print("2. TRANSFORM: Extracting metadata with GPT-4...")
    try:
        extractor = MetadataExtractor()
        metadata, validation = extractor.extract_with_validation(text)

        print(f"   Confidence: {validation.confidence}%")
        print(f"   Valid: {validation.is_valid}")
        print(f"   Document: {metadata.document_type} {metadata.number}")
        print(f"   Title: {metadata.title}")
        print(f"   Date: {metadata.date_enacted}")
        print(f"   Authority: {metadata.authority}")
        print(f"   Country: {metadata.country}, Language: {metadata.language}\n")

        # Step 3: Transform (T in ETL) - Extract Preamble
        print("3. TRANSFORM: Extracting preamble structure...")
        numbered_text, _ = extract_text_with_line_numbers(pdf_path)
        preamble_identifier = PreambleIdentifier()
        preamble_location = preamble_identifier.identify_preamble(numbered_text)

        preamble_text = extract_lines_range(
            pdf_path,
            preamble_location.start_line,
            preamble_location.end_line
        )

        print(f"   Preamble identified (lines {preamble_location.start_line}-{preamble_location.end_line})")
        print(f"   Confidence: {preamble_location.confidence}%")
        print(f"   Legal basis statements: {len(preamble_location.legal_basis)}")
        print(f"   Preamble text: {len(preamble_text)} characters\n")

        # Step 4: Transform (T in ETL) - Extract Recitals
        print("4. TRANSFORM: Extracting recitals structure...")
        recitals_identifier = RecitalsIdentifier()
        recitals_location = recitals_identifier.identify_recitals(numbered_text)

        recitals_text = extract_lines_range(
            pdf_path,
            recitals_location.start_line,
            recitals_location.end_line
        )

        recitals_summary = get_recitals_summary(recitals_text)
        recitals_xml = build_recitals_xml(recitals_text)

        print(f"   Recitals identified (lines {recitals_location.start_line}-{recitals_location.end_line})")
        print(f"   Confidence: {recitals_location.confidence}%")
        print(f"   Parsed recitals: {recitals_summary['count']}")
        print(f"   Recital numbers: ({recitals_summary['first_number']}) to ({recitals_summary['last_number']})")
        print(f"   Recitals text: {len(recitals_text)} characters\n")

        # Step 5: Transform (T in ETL) - Generate Akoma Ntoso
        print("5. TRANSFORM: Generating Akoma Ntoso XML...")

        # Create root element
        root_xml = create_akoma_ntoso_root()
        print("   Root element created")

        # Create FRBR metadata
        frbr_xml = build_frbr_metadata(metadata)
        print("   FRBR metadata generated")

        # Combine into complete XML structure with preamble and recitals
        preamble_xml = f'''    <preface>
      <p>{preamble_text.replace('\n', '</p>\n      <p>')}</p>
    </preface>'''

        # Use the generated recitals XML (already formatted)
        formatted_recitals_xml = '\n'.join('    ' + line for line in recitals_xml.split('\n') if line.strip())

        complete_xml = f'''<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="{metadata.document_type.replace(' ', '_')}">
    {frbr_xml}
{preamble_xml}
{formatted_recitals_xml}
    <body>
      <!-- Document chapters, articles will go here -->
    </body>
  </act>
</akomaNtoso>'''

        # Step 6: Load (L in ETL) - Save XML to file
        print("6. LOAD: Saving XML output...")

        # Create output directory
        import os
        os.makedirs("output", exist_ok=True)

        # Save complete XML
        xml_filename = f"output/DORA_{metadata.number.replace('/', '_')}_akoma_ntoso.xml"
        with open(xml_filename, 'w', encoding='utf-8') as f:
            f.write(complete_xml)

        # Save metadata as JSON for reference
        import json
        metadata_filename = f"output/DORA_{metadata.number.replace('/', '_')}_metadata.json"
        with open(metadata_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'document_type': metadata.document_type,
                'number': metadata.number,
                'title': metadata.title,
                'date_enacted': str(metadata.date_enacted),
                'date_published': str(metadata.date_published) if metadata.date_published else None,
                'authority': metadata.authority,
                'country': metadata.country,
                'language': metadata.language,
                'official_journal': metadata.official_journal,
                'validation_confidence': validation.confidence,
                'validation_valid': validation.is_valid,
                'preamble': {
                    'start_line': preamble_location.start_line,
                    'end_line': preamble_location.end_line,
                    'confidence': preamble_location.confidence,
                    'legal_basis_count': len(preamble_location.legal_basis)
                },
                'recitals': {
                    'start_line': recitals_location.start_line,
                    'end_line': recitals_location.end_line,
                    'confidence': recitals_location.confidence,
                    'parsed_count': recitals_summary['count'],
                    'first_number': recitals_summary['first_number'],
                    'last_number': recitals_summary['last_number']
                }
            }, f, indent=2)

        print(f"   [OK] Complete XML saved to: {xml_filename}")
        print(f"   [OK] Metadata saved to: {metadata_filename}")
        print("   [OK] ETL Pipeline Complete!")
        print("   [OK] Ready for document body processing\n")

        print("=== Next Steps ===")
        print("- Add recitals extraction")
        print("- Add document body structure parsing (chapters, articles)")
        print("- Complete XML generation pipeline")

    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure OPENROUTER_API_KEY is set in .env file")


if __name__ == "__main__":
    main()
