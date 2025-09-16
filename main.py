import sys
import os
sys.path.append('.')

from src.pdf_extractor import extract_text, extract_text_with_line_numbers, extract_lines_range
from src.transform.metadata_extractor import MetadataExtractor
from src.transform.preamble_identifier import PreambleIdentifier
from src.transform.recitals_identifier import RecitalsIdentifier
from src.transform.recitals_builder import build_recitals_xml, get_recitals_summary
from src.transform.chapter_identifier import ChapterIdentifier
from src.transform.chapter_builder import build_chapters_xml, get_chapters_summary, build_chapters_with_sections_xml
from src.transform.section_identifier import SectionIdentifier
from src.transform.frbr_builder import build_frbr_metadata
from src.transform.akn_builder import create_akoma_ntoso_root
from src.transform.verification_integration import VerificationIntegration

def extract_chapters_content(pdf_path: str, chapters: list) -> list:
    """
    Extract content for each chapter with boundaries and statistics.

    Args:
        pdf_path: Path to PDF file
        chapters: List of ChapterInfo objects

    Returns:
        List of chapters with content and statistics
    """
    if not chapters:
        return []

    # Sort chapters by start_line to ensure proper order
    sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

    chapters_with_content = []

    for i, chapter in enumerate(sorted_chapters):
        # Determine end line for this chapter
        if i < len(sorted_chapters) - 1:
            # End line is just before next chapter starts
            end_line = sorted_chapters[i + 1].start_line - 1
        else:
            # For last chapter, we need to determine document end
            # For now, use a large number that will capture everything
            end_line = 999999

        # Extract content for this chapter
        try:
            content = extract_lines_range(pdf_path, chapter.start_line, end_line)

            # Calculate statistics
            word_count = len(content.split()) if content else 0
            line_count = len(content.split('\n')) if content else 0

            chapter_with_content = {
                "chapter_number": chapter.chapter_number,
                "title": chapter.title,
                "start_line": chapter.start_line,
                "end_line": end_line,
                "page_number": chapter.page_number,
                "confidence": chapter.confidence,
                "content": content,
                "word_count": word_count,
                "line_count": line_count
            }

            chapters_with_content.append(chapter_with_content)

        except Exception as e:
            print(f"     Error extracting content for Chapter {chapter.chapter_number}: {e}")
            # Add chapter without content
            chapter_with_content = {
                "chapter_number": chapter.chapter_number,
                "title": chapter.title,
                "start_line": chapter.start_line,
                "end_line": end_line,
                "page_number": chapter.page_number,
                "confidence": chapter.confidence,
                "content": "",
                "word_count": 0,
                "line_count": 0,
                "error": str(e)
            }
            chapters_with_content.append(chapter_with_content)

    return chapters_with_content

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

        # Step 5: Transform (T in ETL) - Extract Chapters
        print("5. TRANSFORM: Extracting chapters structure...")
        chapter_identifier = ChapterIdentifier()
        chapters = chapter_identifier.extract_all_chapters_auto(
            pdf_path,
            max_workers=3
        )

        chapters_summary = get_chapters_summary(chapters)
        chapters_xml = build_chapters_xml(chapters)

        print(f"   Chapters found: {chapters_summary['count']}")
        print(f"   Chapter range: {chapters_summary['first_chapter']} to {chapters_summary['last_chapter']}")
        print(f"   Sequence: {' → '.join(chapters_summary['chapter_sequence'])}")
        print(f"   Avg confidence: {chapters_summary['confidence_avg']}%")
        print(f"   Line range: {chapters_summary['line_range'][0]} to {chapters_summary['line_range'][1]}\n")

        # Extract chapter content for inspection
        print("   Extracting chapter content...")
        chapters_with_content = extract_chapters_content(pdf_path, chapters)
        print(f"   Content extracted for {len(chapters_with_content)} chapters")

        # AUTOMATIC VERIFICATION: Verify chapter extraction accuracy
        print("   Verifying chapter extraction accuracy...")
        verification_integration = VerificationIntegration(pdf_path, "DORA_2022_2554")
        verification_report = verification_integration.verify_and_save_chapters(chapters, chapters_with_content)

        # Check if verification passed - stop pipeline if accuracy too low
        if not verification_integration.should_proceed_with_pipeline(verification_report):
            print("   Stopping pipeline due to low verification accuracy.")
            return

        print("   Chapter verification completed successfully!\n")

        # Step 5.5: Transform (T in ETL) - Extract Sections
        print("5.5. TRANSFORM: Extracting sections within chapters...")
        section_identifier = SectionIdentifier()
        sections = section_identifier.extract_sections_within_chapters(pdf_path, chapters)
        sections_validation = section_identifier.validate_sections(sections)

        print(f"   Sections found: {sections_validation['total_sections']}")
        if sections_validation['chapters_with_sections']:
            print(f"   Chapters with sections: {', '.join(sections_validation['chapters_with_sections'])}")
            for chapter, section_nums in sections_validation['sections_by_chapter'].items():
                print(f"   Chapter {chapter}: {', '.join(section_nums)}")
        else:
            print("   No sections found in any chapters")

        # AUTOMATIC VERIFICATION: Verify section extraction accuracy (if sections exist)
        if sections:
            print("   Verifying section extraction accuracy...")
            section_verification_report = verification_integration.verify_and_save_sections(sections, chapters)

            # Check if section verification passed
            if not verification_integration.should_proceed_with_pipeline(section_verification_report):
                print("   Stopping pipeline due to low section verification accuracy.")
                return

            print("   Section verification completed successfully!\n")
        else:
            print("   No sections to verify.\n")

        # Step 6: Transform (T in ETL) - Generate Akoma Ntoso
        print("6. TRANSFORM: Generating Akoma Ntoso XML...")

        # Create root element
        root_xml = create_akoma_ntoso_root()
        print("   Root element created")

        # Create FRBR metadata
        frbr_xml = build_frbr_metadata(metadata)
        print("   FRBR metadata generated")

        # Combine into complete XML structure with preamble, recitals, and chapters
        preamble_xml = f'''    <preface>
      <p>{preamble_text.replace('\n', '</p>\n      <p>')}</p>
    </preface>'''

        # Use the generated recitals XML (already formatted)
        formatted_recitals_xml = '\n'.join('    ' + line for line in recitals_xml.split('\n') if line.strip())

        # Generate chapters XML with sections
        chapters_with_sections_xml = build_chapters_with_sections_xml(chapters, sections)
        formatted_chapters_xml = '\n'.join('    ' + line for line in chapters_with_sections_xml.split('\n') if line.strip())

        complete_xml = f'''<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act name="{metadata.document_type.replace(' ', '_')}">
    {frbr_xml}
{preamble_xml}
{formatted_recitals_xml}
{formatted_chapters_xml}
  </act>
</akomaNtoso>'''

        # Step 7: Load (L in ETL) - Save XML to file
        print("7. LOAD: Saving XML output...")

        # Create output directory
        import os
        import json
        from datetime import datetime
        os.makedirs("output", exist_ok=True)

        # Save chapters with content as JSON
        chapters_json_data = {
            "document": f"DORA_{metadata.number.replace('/', '_')}",
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "extraction_timestamp": datetime.now().isoformat(),
            "chapters": chapters_with_content,
            "summary": {
                "total_chapters": len(chapters_with_content),
                "total_lines": sum(ch.get('line_count', 0) for ch in chapters_with_content),
                "total_words": sum(ch.get('word_count', 0) for ch in chapters_with_content),
                "chapters_with_content": len([ch for ch in chapters_with_content if ch.get('content', '').strip()]),
                "chapters_with_errors": len([ch for ch in chapters_with_content if 'error' in ch])
            }
        }

        chapters_json_filename = f"output/DORA_{metadata.number.replace('/', '_')}_chapters_with_content.json"
        with open(chapters_json_filename, 'w', encoding='utf-8') as f:
            json.dump(chapters_json_data, f, indent=2, ensure_ascii=False)

        # Save sections as JSON
        sections_json_data = {
            "document": f"DORA_{metadata.number.replace('/', '_')}",
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "extraction_timestamp": datetime.now().isoformat(),
            "sections": [
                {
                    "section_number": section.section_number,
                    "parent_chapter": section.parent_chapter,
                    "start_line": section.start_line,
                    "confidence": section.confidence
                }
                for section in sections
            ],
            "summary": {
                "total_sections": sections_validation['total_sections'],
                "chapters_with_sections": sections_validation['chapters_with_sections'],
                "sections_by_chapter": sections_validation['sections_by_chapter']
            }
        }

        sections_json_filename = f"output/DORA_{metadata.number.replace('/', '_')}_sections.json"
        with open(sections_json_filename, 'w', encoding='utf-8') as f:
            json.dump(sections_json_data, f, indent=2, ensure_ascii=False)

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
                },
                'chapters': {
                    'count': chapters_summary['count'],
                    'first_chapter': chapters_summary['first_chapter'],
                    'last_chapter': chapters_summary['last_chapter'],
                    'sequence': chapters_summary['chapter_sequence'],
                    'confidence_avg': chapters_summary['confidence_avg'],
                    'line_range': chapters_summary['line_range']
                }
            }, f, indent=2)

        print(f"   [OK] Complete XML saved to: {xml_filename}")
        print(f"   [OK] Metadata saved to: {metadata_filename}")
        print(f"   [OK] Chapters with content saved to: {chapters_json_filename}")
        print(f"   [OK] Sections saved to: {sections_json_filename}")
        print("   [OK] ETL Pipeline Complete!")

    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure OPENROUTER_API_KEY is set in .env file")


if __name__ == "__main__":
    main()
