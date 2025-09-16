"""
Chapter verifier for validating extracted chapters against PDF source.
"""

from typing import Dict, List, Any, Optional
from .base_verifier import BaseVerifier
from ..models import ChapterInfo


class ChapterVerifier(BaseVerifier):
    """Verifier for chapter extraction accuracy"""

    def __init__(self, pdf_path: str):
        """Initialize chapter verifier"""
        super().__init__(pdf_path)

    def verify_component(self, chapter: ChapterInfo) -> Dict[str, Any]:
        """
        Verify a single chapter against PDF source.

        Args:
            chapter: ChapterInfo object to verify

        Returns:
            Verification result dictionary
        """
        result = {
            "chapter_number": chapter.chapter_number,
            "title": chapter.title,
            "reported_start_line": chapter.start_line,
            "reported_page": chapter.page_number,
            "confidence_score": chapter.confidence,
            "verification_details": {}
        }

        # Get PDF text at reported line
        pdf_text_at_line = self.get_pdf_text_at_line(chapter.start_line)
        result["pdf_text_at_line"] = pdf_text_at_line

        # Verify chapter header (should be "CHAPTER X")
        expected_header = f"CHAPTER {chapter.chapter_number}"
        header_match, header_confidence = self.check_text_match(expected_header, pdf_text_at_line)

        result["verification_details"]["header_match"] = {
            "expected": expected_header,
            "found": pdf_text_at_line,
            "exact_match": header_match,
            "confidence": header_confidence
        }

        # Verify chapter title (usually on next line or nearby)
        title_verified = False
        title_confidence = 0.0
        title_found_at_line = None

        # Check next few lines for title
        for offset in range(1, 5):
            check_line = chapter.start_line + offset
            pdf_text_title = self.get_pdf_text_at_line(check_line)

            if pdf_text_title:
                title_match, title_conf = self.check_text_match(
                    chapter.title, pdf_text_title, fuzzy=True
                )
                if title_match and title_conf > title_confidence:
                    title_verified = title_match
                    title_confidence = title_conf
                    title_found_at_line = check_line
                    break

        result["verification_details"]["title_match"] = {
            "expected": chapter.title,
            "found_at_line": title_found_at_line,
            "found_text": self.get_pdf_text_at_line(title_found_at_line) if title_found_at_line else "",
            "exact_match": title_verified,
            "confidence": title_confidence
        }

        # Overall verification
        overall_match = header_match and title_verified
        overall_confidence = min(header_confidence, title_confidence) if title_verified else header_confidence

        result["exact_match"] = overall_match
        result["confidence"] = overall_confidence
        result["verification_status"] = "PASS" if overall_match else "FAIL"

        # Add any issues
        issues = []
        if not header_match:
            issues.append(f"Chapter header mismatch at line {chapter.start_line}")
        if not title_verified:
            issues.append(f"Chapter title not found near line {chapter.start_line}")

        result["issues"] = issues

        return result

    def verify_all(self, chapters: List[ChapterInfo]) -> Dict[str, Any]:
        """
        Verify all chapters and generate comprehensive report.

        Args:
            chapters: List of ChapterInfo objects to verify

        Returns:
            Complete verification report
        """
        # Generate base metadata
        report = self.generate_base_metadata("chapters")

        # Verify each chapter
        verification_results = []
        for chapter in chapters:
            chapter_result = self.verify_component(chapter)
            verification_results.append(chapter_result)

        # Calculate accuracy metrics
        accuracy_metrics = self.calculate_accuracy_metrics(verification_results)

        # Add chapter-specific analysis
        chapter_analysis = self._analyze_chapter_sequence(chapters, verification_results)

        # Compile final report
        report.update({
            "chapters": verification_results,
            "accuracy_metrics": accuracy_metrics,
            "chapter_analysis": chapter_analysis,
            "summary": {
                "total_chapters_verified": len(verification_results),
                "successful_verifications": accuracy_metrics["exact_matches"],
                "failed_verifications": len(verification_results) - accuracy_metrics["exact_matches"],
                "overall_accuracy": accuracy_metrics["accuracy_percentage"],
                "recommendation": self._get_recommendation(accuracy_metrics["accuracy_percentage"])
            }
        })

        return report

    def _analyze_chapter_sequence(self, chapters: List[ChapterInfo], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze chapter sequence and numbering.

        Args:
            chapters: List of chapters
            results: Verification results

        Returns:
            Chapter sequence analysis
        """
        # Sort by start line
        sorted_chapters = sorted(chapters, key=lambda c: c.start_line)

        # Check sequence
        roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
        expected_sequence = roman_numerals[:len(sorted_chapters)]
        actual_sequence = [c.chapter_number for c in sorted_chapters]

        sequence_correct = expected_sequence == actual_sequence

        # Check line ordering
        line_numbers = [c.start_line for c in sorted_chapters]
        line_ordering_correct = line_numbers == sorted(line_numbers)

        return {
            "total_chapters": len(chapters),
            "expected_sequence": expected_sequence,
            "actual_sequence": actual_sequence,
            "sequence_correct": sequence_correct,
            "line_ordering_correct": line_ordering_correct,
            "line_numbers": line_numbers,
            "gaps_in_sequence": [
                expected for expected, actual in zip(expected_sequence, actual_sequence)
                if expected != actual
            ]
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
            return "EXCELLENT: Chapter extraction is highly accurate. Safe to proceed."
        elif accuracy_percentage >= 85:
            return "GOOD: Chapter extraction is mostly accurate. Review failed items."
        elif accuracy_percentage >= 70:
            return "WARNING: Chapter extraction has some issues. Manual review recommended."
        else:
            return "CRITICAL: Chapter extraction has major issues. Manual intervention required."

    def verify_chapter_boundaries(self, chapters_with_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify chapter boundary accuracy by checking content consistency.

        Args:
            chapters_with_content: Chapters with extracted content

        Returns:
            Boundary verification results
        """
        boundary_results = []

        for i, chapter in enumerate(chapters_with_content):
            result = {
                "chapter_number": chapter["chapter_number"],
                "start_line": chapter["start_line"],
                "end_line": chapter.get("end_line"),
                "content_lines": chapter.get("line_count", 0)
            }

            # Check if chapter content starts with expected chapter header
            content = chapter.get("content", "")
            if content:
                first_line = content.split('\n')[0].strip()
                expected_start = f"CHAPTER {chapter['chapter_number']}"
                start_match = expected_start in first_line

                result["content_starts_correctly"] = start_match
                result["actual_first_line"] = first_line
            else:
                result["content_starts_correctly"] = False
                result["actual_first_line"] = ""

            # Check for content overlap (next chapter's content shouldn't start in this chapter)
            if i < len(chapters_with_content) - 1:
                next_chapter = chapters_with_content[i + 1]
                next_expected_start = f"CHAPTER {next_chapter['chapter_number']}"

                # Check if next chapter header appears in current chapter content
                overlap_detected = next_expected_start in content
                result["overlap_with_next"] = overlap_detected

            boundary_results.append(result)

        return {
            "boundary_verification": boundary_results,
            "summary": {
                "total_boundaries_checked": len(boundary_results),
                "correct_start_boundaries": sum(1 for r in boundary_results if r.get("content_starts_correctly", False)),
                "detected_overlaps": sum(1 for r in boundary_results if r.get("overlap_with_next", False))
            }
        }