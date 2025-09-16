"""
Integration module for automatic verification in the ETL pipeline.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from .verification import ChapterVerifier, SectionVerifier
from .models import ChapterInfo, SectionInfo


class VerificationIntegration:
    """Handles integration of verification into the main ETL pipeline"""

    def __init__(self, pdf_path: str, regulation_name: str):
        """
        Initialize verification integration.

        Args:
            pdf_path: Path to the PDF file
            regulation_name: Name of the regulation (for output files)
        """
        self.pdf_path = pdf_path
        self.regulation_name = regulation_name
        self.output_dir = "output"

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def verify_and_save_chapters(
        self,
        chapters: List[ChapterInfo],
        chapters_with_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify chapters and save results with verification metadata.

        Args:
            chapters: List of ChapterInfo objects
            chapters_with_content: Chapters with extracted content

        Returns:
            Verification report
        """
        print(f"\n--- Chapter Verification for {self.regulation_name} ---")

        # Initialize chapter verifier
        chapter_verifier = ChapterVerifier(self.pdf_path)

        # Verify chapters
        verification_report = chapter_verifier.verify_all(chapters)

        # Verify boundaries if content is available
        if chapters_with_content:
            boundary_verification = chapter_verifier.verify_chapter_boundaries(chapters_with_content)
            verification_report["boundary_verification"] = boundary_verification

        # Print summary
        accuracy = verification_report["accuracy_metrics"]["accuracy_percentage"]
        total_chapters = verification_report["summary"]["total_chapters_verified"]
        successful = verification_report["summary"]["successful_verifications"]

        print(f"Chapter Verification Results:")
        print(f"  Total Chapters: {total_chapters}")
        print(f"  Successful Verifications: {successful}")
        print(f"  Accuracy: {accuracy:.1f}%")
        print(f"  Status: {verification_report['summary']['recommendation']}")

        # Save verification report
        verification_file = os.path.join(
            self.output_dir,
            f"{self.regulation_name}_chapter_verification.json"
        )

        with open(verification_file, 'w', encoding='utf-8') as f:
            json.dump(verification_report, f, indent=2, ensure_ascii=False)

        print(f"  Saved verification report: {verification_file}")

        # Save enhanced chapters with verification
        enhanced_chapters = self._enhance_chapters_with_verification(
            chapters_with_content or self._convert_chapters_to_dict(chapters),
            verification_report["chapters"]
        )

        enhanced_file = os.path.join(
            self.output_dir,
            f"{self.regulation_name}_chapters_with_verification.json"
        )

        enhanced_data = {
            "document": self.regulation_name,
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "extraction_timestamp": datetime.now().isoformat(),
            "verification_summary": {
                "accuracy_percentage": accuracy,
                "total_chapters": total_chapters,
                "successful_verifications": successful,
                "verification_timestamp": verification_report["verification_metadata"]["verification_timestamp"]
            },
            "chapters": enhanced_chapters
        }

        with open(enhanced_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

        print(f"  Saved enhanced chapters: {enhanced_file}")

        # Check if accuracy meets minimum threshold
        if accuracy < 95:
            print(f"\n⚠️  WARNING: Chapter accuracy ({accuracy:.1f}%) is below 95% threshold")
            print(f"   Please review verification report for details")

            # Log failed verifications
            failed_chapters = [
                ch for ch in verification_report["chapters"]
                if not ch.get("exact_match", False)
            ]

            if failed_chapters:
                print(f"   Failed Chapters:")
                for failed in failed_chapters:
                    print(f"     - Chapter {failed['chapter_number']}: {failed.get('issues', [])}")

        return verification_report

    def _enhance_chapters_with_verification(
        self,
        chapters_data: List[Dict[str, Any]],
        verification_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance chapter data with verification results.

        Args:
            chapters_data: Original chapter data
            verification_results: Verification results

        Returns:
            Enhanced chapter data with verification info
        """
        # Create lookup for verification results
        verification_lookup = {
            result["chapter_number"]: result
            for result in verification_results
        }

        enhanced_chapters = []
        for chapter in chapters_data:
            enhanced_chapter = chapter.copy()

            # Add verification data
            chapter_num = chapter.get("chapter_number")
            if chapter_num in verification_lookup:
                verification = verification_lookup[chapter_num]
                enhanced_chapter["verification"] = {
                    "exact_match": verification.get("exact_match", False),
                    "confidence": verification.get("confidence", 0),
                    "verification_status": verification.get("verification_status", "UNKNOWN"),
                    "issues": verification.get("issues", []),
                    "header_verified": verification["verification_details"]["header_match"]["exact_match"],
                    "title_verified": verification["verification_details"]["title_match"]["exact_match"]
                }
            else:
                enhanced_chapter["verification"] = {
                    "exact_match": False,
                    "confidence": 0,
                    "verification_status": "NOT_VERIFIED",
                    "issues": ["No verification data available"]
                }

            enhanced_chapters.append(enhanced_chapter)

        return enhanced_chapters

    def _convert_chapters_to_dict(self, chapters: List[ChapterInfo]) -> List[Dict[str, Any]]:
        """
        Convert ChapterInfo objects to dictionaries.

        Args:
            chapters: List of ChapterInfo objects

        Returns:
            List of chapter dictionaries
        """
        return [
            {
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "start_line": ch.start_line,
                "page_number": ch.page_number,
                "confidence": ch.confidence
            }
            for ch in chapters
        ]

    def generate_accuracy_report(self, verification_report: Dict[str, Any]) -> str:
        """
        Generate a human-readable accuracy report.

        Args:
            verification_report: Verification report data

        Returns:
            Formatted accuracy report string
        """
        metrics = verification_report["accuracy_metrics"]
        summary = verification_report["summary"]

        report = f"""
=== CHAPTER VERIFICATION REPORT ===
Regulation: {self.regulation_name}
PDF: {os.path.basename(self.pdf_path)}
Verification Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

ACCURACY METRICS:
- Total Chapters: {metrics['total_items']}
- Exact Matches: {metrics['exact_matches']}
- Accuracy: {metrics['accuracy_percentage']:.1f}%
- Average Confidence: {metrics['average_confidence']:.1f}%

CONFIDENCE DISTRIBUTION:
- High (95-100%): {metrics['confidence_distribution']['high (95-100%)']}
- Medium (70-94%): {metrics['confidence_distribution']['medium (70-94%)']}
- Low (<70%): {metrics['confidence_distribution']['low (<70%)']}

RECOMMENDATION: {summary['recommendation']}
        """

        # Add failed chapters if any
        failed_chapters = [
            ch for ch in verification_report["chapters"]
            if not ch.get("exact_match", False)
        ]

        if failed_chapters:
            report += "\nFAILED VERIFICATIONS:\n"
            for failed in failed_chapters:
                report += f"- Chapter {failed['chapter_number']}: {', '.join(failed.get('issues', []))}\n"

        return report.strip()

    def should_proceed_with_pipeline(self, verification_report: Dict[str, Any]) -> bool:
        """
        Determine if pipeline should continue based on verification results.

        Args:
            verification_report: Verification report

        Returns:
            True if pipeline should continue, False otherwise
        """
        accuracy = verification_report["accuracy_metrics"]["accuracy_percentage"]

        # Configurable thresholds
        critical_threshold = 50  # Below this, stop pipeline
        warning_threshold = 85   # Below this, show warnings but continue

        if accuracy < critical_threshold:
            print(f"\n❌ CRITICAL: Chapter accuracy ({accuracy:.1f}%) is too low. Stopping pipeline.")
            return False
        elif accuracy < warning_threshold:
            print(f"\n⚠️  WARNING: Chapter accuracy ({accuracy:.1f}%) is below recommended threshold.")
            print("   Continuing but manual review is recommended.")

        return True

    def verify_and_save_sections(
        self,
        sections: List[SectionInfo],
        chapters: List[ChapterInfo]
    ) -> Dict[str, Any]:
        """
        Verify sections and save results with verification metadata.

        Args:
            sections: List of SectionInfo objects
            chapters: List of ChapterInfo objects for boundary validation

        Returns:
            Verification report
        """
        print(f"\n--- Section Verification for {self.regulation_name} ---")

        # Initialize section verifier
        section_verifier = SectionVerifier(self.pdf_path)

        # Verify sections
        verification_report = section_verifier.verify_all(sections, chapters)

        # Add hierarchy validation
        hierarchy_validation = section_verifier.verify_section_hierarchy(sections, chapters)
        verification_report["hierarchy_validation"] = hierarchy_validation

        # Print summary
        accuracy = verification_report["accuracy_metrics"]["accuracy_percentage"]
        total_sections = verification_report["summary"]["total_sections_verified"]
        successful = verification_report["summary"]["successful_verifications"]

        print(f"Section Verification Results:")
        print(f"  Total Sections: {total_sections}")
        print(f"  Successful Verifications: {successful}")
        print(f"  Accuracy: {accuracy:.1f}%")
        print(f"  Chapters with Sections: {', '.join(verification_report['section_analysis']['chapters_with_sections'])}")
        print(f"  Status: {verification_report['summary']['recommendation']}")

        # Save verification report
        verification_file = os.path.join(
            self.output_dir,
            f"{self.regulation_name}_section_verification.json"
        )

        with open(verification_file, 'w', encoding='utf-8') as f:
            json.dump(verification_report, f, indent=2, ensure_ascii=False)

        print(f"  Saved verification report: {verification_file}")

        # Save enhanced sections with verification
        enhanced_sections = self._enhance_sections_with_verification(
            self._convert_sections_to_dict(sections),
            verification_report["sections"]
        )

        enhanced_file = os.path.join(
            self.output_dir,
            f"{self.regulation_name}_sections_with_verification.json"
        )

        enhanced_data = {
            "document": self.regulation_name,
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "extraction_timestamp": datetime.now().isoformat(),
            "verification_summary": {
                "accuracy_percentage": accuracy,
                "total_sections": total_sections,
                "successful_verifications": successful,
                "verification_timestamp": verification_report["verification_metadata"]["verification_timestamp"]
            },
            "sections": enhanced_sections
        }

        with open(enhanced_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

        print(f"  Saved enhanced sections: {enhanced_file}")

        # Check if accuracy meets minimum threshold
        if accuracy < 95:
            print(f"\n⚠️  WARNING: Section accuracy ({accuracy:.1f}%) is below 95% threshold")
            print(f"   Please review verification report for details")

            # Log failed verifications
            failed_sections = [
                sec for sec in verification_report["sections"]
                if not sec.get("exact_match", False)
            ]

            if failed_sections:
                print(f"   Failed Sections:")
                for failed in failed_sections:
                    print(f"     - Chapter {failed['parent_chapter']}, Section {failed['section_number']}: {failed.get('issues', [])}")

        return verification_report

    def _enhance_sections_with_verification(
        self,
        sections_data: List[Dict[str, Any]],
        verification_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance section data with verification results.

        Args:
            sections_data: Original section data
            verification_results: Verification results

        Returns:
            Enhanced section data with verification info
        """
        # Create lookup for verification results
        verification_lookup = {}
        for result in verification_results:
            key = f"{result['parent_chapter']}_{result['section_number']}"
            verification_lookup[key] = result

        enhanced_sections = []
        for section in sections_data:
            enhanced_section = section.copy()

            # Add verification data
            section_key = f"{section.get('parent_chapter')}_{section.get('section_number')}"
            if section_key in verification_lookup:
                verification = verification_lookup[section_key]
                enhanced_section["verification"] = {
                    "exact_match": verification.get("exact_match", False),
                    "confidence": verification.get("confidence", 0),
                    "verification_status": verification.get("verification_status", "UNKNOWN"),
                    "issues": verification.get("issues", []),
                    "header_verified": verification["verification_details"]["header_match"]["exact_match"]
                }
            else:
                enhanced_section["verification"] = {
                    "exact_match": False,
                    "confidence": 0,
                    "verification_status": "NOT_VERIFIED",
                    "issues": ["No verification data available"]
                }

            enhanced_sections.append(enhanced_section)

        return enhanced_sections

    def _convert_sections_to_dict(self, sections: List[SectionInfo]) -> List[Dict[str, Any]]:
        """
        Convert SectionInfo objects to dictionaries.

        Args:
            sections: List of SectionInfo objects

        Returns:
            List of section dictionaries
        """
        return [
            {
                "section_number": sec.section_number,
                "parent_chapter": sec.parent_chapter,
                "start_line": sec.start_line,
                "confidence": sec.confidence
            }
            for sec in sections
        ]