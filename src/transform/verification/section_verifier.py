"""
Section verifier for validating extracted sections against PDF source.
"""

from typing import Dict, List, Any, Optional
from .base_verifier import BaseVerifier
from ..models import SectionInfo, ChapterInfo


class SectionVerifier(BaseVerifier):
    """Verifier for section extraction accuracy"""

    def __init__(self, pdf_path: str):
        """Initialize section verifier"""
        super().__init__(pdf_path)

    def verify_component(self, section: SectionInfo) -> Dict[str, Any]:
        """
        Verify a single section against PDF source.

        Args:
            section: SectionInfo object to verify

        Returns:
            Verification result dictionary
        """
        result = {
            "section_number": section.section_number,
            "parent_chapter": section.parent_chapter,
            "reported_start_line": section.start_line,
            "confidence_score": section.confidence,
            "verification_details": {}
        }

        # Get PDF text at reported line
        pdf_text_at_line = self.get_pdf_text_at_line(section.start_line)
        result["pdf_text_at_line"] = pdf_text_at_line

        # Verify section header (should be "Section X")
        expected_header = f"Section {section.section_number}"
        header_match, header_confidence = self.check_text_match(expected_header, pdf_text_at_line)

        result["verification_details"]["header_match"] = {
            "expected": expected_header,
            "found": pdf_text_at_line,
            "exact_match": header_match,
            "confidence": header_confidence
        }

        # Overall verification
        result["exact_match"] = header_match
        result["confidence"] = header_confidence
        result["verification_status"] = "PASS" if header_match else "FAIL"

        # Add any issues
        issues = []
        if not header_match:
            issues.append(f"Section header mismatch at line {section.start_line}")

        result["issues"] = issues

        return result

    def verify_all(self, sections: List[SectionInfo], chapters: List[ChapterInfo] = None) -> Dict[str, Any]:
        """
        Verify all sections and generate comprehensive report.

        Args:
            sections: List of SectionInfo objects to verify
            chapters: List of ChapterInfo objects for boundary validation

        Returns:
            Complete verification report
        """
        # Generate base metadata
        report = self.generate_base_metadata("sections")

        # Verify each section
        verification_results = []
        for section in sections:
            section_result = self.verify_component(section)
            verification_results.append(section_result)

        # Calculate accuracy metrics
        accuracy_metrics = self.calculate_accuracy_metrics(verification_results)

        # Add section-specific analysis
        section_analysis = self._analyze_section_structure(sections, chapters)
        boundary_analysis = self._analyze_section_boundaries(sections, chapters) if chapters else {}

        # Compile final report
        report.update({
            "sections": verification_results,
            "accuracy_metrics": accuracy_metrics,
            "section_analysis": section_analysis,
            "boundary_analysis": boundary_analysis,
            "summary": {
                "total_sections_verified": len(verification_results),
                "successful_verifications": accuracy_metrics["exact_matches"],
                "failed_verifications": len(verification_results) - accuracy_metrics["exact_matches"],
                "overall_accuracy": accuracy_metrics["accuracy_percentage"],
                "recommendation": self._get_recommendation(accuracy_metrics["accuracy_percentage"])
            }
        })

        return report

    def _analyze_section_structure(self, sections: List[SectionInfo], chapters: List[ChapterInfo] = None) -> Dict[str, Any]:
        """
        Analyze section structure and relationships.

        Args:
            sections: List of sections
            chapters: List of chapters for reference

        Returns:
            Section structure analysis
        """
        # Group sections by chapter
        sections_by_chapter = {}
        for section in sections:
            chapter = section.parent_chapter
            if chapter not in sections_by_chapter:
                sections_by_chapter[chapter] = []
            sections_by_chapter[chapter].append(section)

        # Sort sections within each chapter by start line
        for chapter_num in sections_by_chapter:
            sections_by_chapter[chapter_num].sort(key=lambda s: s.start_line)

        # Analyze sequencing
        sequence_issues = []
        for chapter_num, chapter_sections in sections_by_chapter.items():
            section_numbers = [s.section_number for s in chapter_sections]

            # Check if sections start with "I" and follow roman numeral sequence
            roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
            expected_sequence = roman_numerals[:len(section_numbers)]

            if section_numbers != expected_sequence:
                sequence_issues.append({
                    "chapter": chapter_num,
                    "expected": expected_sequence,
                    "actual": section_numbers
                })

        return {
            "total_sections": len(sections),
            "chapters_with_sections": list(sections_by_chapter.keys()),
            "sections_by_chapter": {
                chapter: [s.section_number for s in sects]
                for chapter, sects in sections_by_chapter.items()
            },
            "sections_per_chapter": {
                chapter: len(sects) for chapter, sects in sections_by_chapter.items()
            },
            "sequence_correct": len(sequence_issues) == 0,
            "sequence_issues": sequence_issues
        }

    def _analyze_section_boundaries(self, sections: List[SectionInfo], chapters: List[ChapterInfo]) -> Dict[str, Any]:
        """
        Analyze section boundaries within chapters.

        Args:
            sections: List of sections
            chapters: List of chapters

        Returns:
            Boundary analysis results
        """
        # Create chapter boundary lookup
        chapter_boundaries = {}
        sorted_chapters = sorted(chapters, key=lambda ch: ch.start_line)

        for i, chapter in enumerate(sorted_chapters):
            start_line = chapter.start_line
            end_line = sorted_chapters[i + 1].start_line - 1 if i + 1 < len(sorted_chapters) else 999999
            chapter_boundaries[chapter.chapter_number] = (start_line, end_line)

        # Verify each section is within its parent chapter boundaries
        boundary_results = []
        for section in sections:
            chapter_bounds = chapter_boundaries.get(section.parent_chapter, (0, 999999))
            within_bounds = chapter_bounds[0] <= section.start_line <= chapter_bounds[1]

            result = {
                "section_number": section.section_number,
                "parent_chapter": section.parent_chapter,
                "section_line": section.start_line,
                "chapter_start": chapter_bounds[0],
                "chapter_end": chapter_bounds[1],
                "within_bounds": within_bounds
            }

            if not within_bounds:
                result["issue"] = f"Section {section.section_number} at line {section.start_line} is outside Chapter {section.parent_chapter} bounds ({chapter_bounds[0]}-{chapter_bounds[1]})"

            boundary_results.append(result)

        # Check for section overlaps within chapters
        overlap_issues = []
        sections_by_chapter = {}
        for section in sections:
            chapter = section.parent_chapter
            if chapter not in sections_by_chapter:
                sections_by_chapter[chapter] = []
            sections_by_chapter[chapter].append(section)

        for chapter_num, chapter_sections in sections_by_chapter.items():
            # Sort by start line
            sorted_sections = sorted(chapter_sections, key=lambda s: s.start_line)

            for i in range(len(sorted_sections) - 1):
                current_section = sorted_sections[i]
                next_section = sorted_sections[i + 1]

                # Sections should not be too close (need some content between them)
                line_gap = next_section.start_line - current_section.start_line
                if line_gap < 10:  # Arbitrary minimum gap
                    overlap_issues.append({
                        "chapter": chapter_num,
                        "section1": current_section.section_number,
                        "section2": next_section.section_number,
                        "line1": current_section.start_line,
                        "line2": next_section.start_line,
                        "gap": line_gap
                    })

        return {
            "boundary_checks": boundary_results,
            "sections_within_bounds": sum(1 for r in boundary_results if r["within_bounds"]),
            "sections_outside_bounds": sum(1 for r in boundary_results if not r["within_bounds"]),
            "boundary_violations": [r for r in boundary_results if not r["within_bounds"]],
            "overlap_issues": overlap_issues,
            "total_overlap_issues": len(overlap_issues)
        }

    def _get_recommendation(self, accuracy_percentage: float) -> str:
        """
        Get recommendation based on accuracy percentage.

        Args:
            accuracy_percentage: Overall accuracy percentage

        Returns:
            Recommendation string
        """
        if accuracy_percentage >= 95:
            return "EXCELLENT: Section extraction is highly accurate. Safe to proceed."
        elif accuracy_percentage >= 85:
            return "GOOD: Section extraction is mostly accurate. Review failed items."
        elif accuracy_percentage >= 70:
            return "WARNING: Section extraction has some issues. Manual review recommended."
        else:
            return "CRITICAL: Section extraction has major issues. Manual intervention required."

    def verify_section_hierarchy(self, sections: List[SectionInfo], chapters: List[ChapterInfo]) -> Dict[str, Any]:
        """
        Verify the complete chapter-section hierarchy.

        Args:
            sections: List of sections
            chapters: List of chapters

        Returns:
            Hierarchy verification results
        """
        hierarchy_results = []

        # Check each chapter
        for chapter in chapters:
            chapter_sections = [s for s in sections if s.parent_chapter == chapter.chapter_number]

            result = {
                "chapter_number": chapter.chapter_number,
                "chapter_line": chapter.start_line,
                "expected_sections": len(chapter_sections) > 0,
                "actual_sections": len(chapter_sections),
                "section_numbers": [s.section_number for s in sorted(chapter_sections, key=lambda x: x.start_line)]
            }

            # Validate section ordering within chapter
            if chapter_sections:
                sorted_sections = sorted(chapter_sections, key=lambda s: s.start_line)
                section_lines = [s.start_line for s in sorted_sections]

                # Check if sections come after chapter start
                sections_after_chapter = all(s_line > chapter.start_line for s_line in section_lines)
                result["sections_after_chapter_start"] = sections_after_chapter

                if not sections_after_chapter:
                    result["issue"] = "Some sections appear before their parent chapter"

            hierarchy_results.append(result)

        return {
            "hierarchy_validation": hierarchy_results,
            "total_chapters_checked": len(chapters),
            "chapters_with_sections": len([r for r in hierarchy_results if r["actual_sections"] > 0]),
            "chapters_without_sections": len([r for r in hierarchy_results if r["actual_sections"] == 0]),
            "hierarchy_issues": [r for r in hierarchy_results if r.get("issue")]
        }