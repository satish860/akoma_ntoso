"""
Base verifier class for PDF extraction verification.
Provides common functionality for verifying extracted content against PDF source.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os


class BaseVerifier(ABC):
    """Base class for all content verifiers"""

    def __init__(self, pdf_path: str):
        """
        Initialize verifier with PDF path.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.pdf_lines: Dict[int, str] = {}
        self.verification_timestamp = datetime.now().isoformat()
        self.load_pdf_lines()

    def load_pdf_lines(self) -> None:
        """Load all lines from PDF with line numbers"""
        from ...pdf_extractor import extract_text_with_line_numbers

        try:
            pdf_text, _ = extract_text_with_line_numbers(self.pdf_path)

            # Parse line-numbered text
            for line in pdf_text.split('\n'):
                if ': ' in line:
                    parts = line.split(': ', 1)
                    try:
                        line_num = int(parts[0])
                        content = parts[1] if len(parts) > 1 else ""
                        self.pdf_lines[line_num] = content
                    except ValueError:
                        continue

            print(f"Loaded {len(self.pdf_lines)} lines from PDF for verification")

        except Exception as e:
            print(f"Error loading PDF lines: {e}")
            self.pdf_lines = {}

    def get_pdf_text_at_line(self, line_number: int) -> str:
        """
        Get text content at specific line number.

        Args:
            line_number: Line number to retrieve

        Returns:
            Text content at that line
        """
        return self.pdf_lines.get(line_number, "")

    def get_pdf_text_range(self, start_line: int, end_line: int) -> str:
        """
        Get text content for a range of lines.

        Args:
            start_line: Starting line number
            end_line: Ending line number

        Returns:
            Concatenated text content for the range
        """
        lines = []
        for line_num in range(start_line, min(end_line + 1, max(self.pdf_lines.keys()) + 1)):
            if line_num in self.pdf_lines:
                lines.append(self.pdf_lines[line_num])
        return '\n'.join(lines)

    def check_text_match(self, expected: str, actual: str, fuzzy: bool = False) -> Tuple[bool, float]:
        """
        Check if expected text matches actual text.

        Args:
            expected: Expected text content
            actual: Actual text content from PDF
            fuzzy: Whether to allow fuzzy matching

        Returns:
            Tuple of (matches, confidence_score)
        """
        if not expected or not actual:
            return False, 0.0

        # Clean and normalize text for comparison
        expected_clean = expected.strip().replace('\n', ' ').replace('  ', ' ')
        actual_clean = actual.strip().replace('\n', ' ').replace('  ', ' ')

        # Exact match
        if expected_clean == actual_clean:
            return True, 100.0

        # Case insensitive match
        if expected_clean.lower() == actual_clean.lower():
            return True, 95.0

        if fuzzy:
            # Simple fuzzy matching - check if expected is contained in actual
            if expected_clean.lower() in actual_clean.lower():
                return True, 80.0

            # Check word overlap
            expected_words = set(expected_clean.lower().split())
            actual_words = set(actual_clean.lower().split())

            if expected_words and actual_words:
                overlap = len(expected_words & actual_words) / len(expected_words | actual_words)
                if overlap > 0.7:
                    return True, overlap * 100

        return False, 0.0

    def generate_base_metadata(self, component_type: str) -> Dict[str, Any]:
        """
        Generate base metadata for verification report.

        Args:
            component_type: Type of component being verified

        Returns:
            Base metadata dictionary
        """
        return {
            "verification_metadata": {
                "component_type": component_type,
                "pdf_file": os.path.basename(self.pdf_path),
                "pdf_path": self.pdf_path,
                "total_pdf_lines": len(self.pdf_lines),
                "verification_timestamp": self.verification_timestamp,
                "verifier_version": "1.0.0"
            }
        }

    def calculate_accuracy_metrics(self, verification_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate accuracy metrics from verification results.

        Args:
            verification_results: List of verification results

        Returns:
            Dictionary with accuracy metrics
        """
        if not verification_results:
            return {
                "total_items": 0,
                "exact_matches": 0,
                "fuzzy_matches": 0,
                "mismatches": 0,
                "accuracy_percentage": 0.0,
                "average_confidence": 0.0
            }

        total_items = len(verification_results)
        exact_matches = sum(1 for r in verification_results if r.get("exact_match", False))
        high_confidence = sum(1 for r in verification_results if r.get("confidence", 0) >= 95)
        medium_confidence = sum(1 for r in verification_results if 70 <= r.get("confidence", 0) < 95)
        low_confidence = sum(1 for r in verification_results if r.get("confidence", 0) < 70)

        total_confidence = sum(r.get("confidence", 0) for r in verification_results)
        average_confidence = total_confidence / total_items if total_items > 0 else 0.0

        return {
            "total_items": total_items,
            "exact_matches": exact_matches,
            "high_confidence_matches": high_confidence,
            "medium_confidence_matches": medium_confidence,
            "low_confidence_matches": low_confidence,
            "accuracy_percentage": (exact_matches / total_items * 100) if total_items > 0 else 0.0,
            "average_confidence": round(average_confidence, 2),
            "confidence_distribution": {
                "high (95-100%)": high_confidence,
                "medium (70-94%)": medium_confidence,
                "low (<70%)": low_confidence
            }
        }

    @abstractmethod
    def verify_component(self, component: Any) -> Dict[str, Any]:
        """
        Verify a single component against PDF source.
        Must be implemented by subclasses.

        Args:
            component: Component to verify

        Returns:
            Verification result dictionary
        """
        pass

    @abstractmethod
    def verify_all(self, components: List[Any]) -> Dict[str, Any]:
        """
        Verify all components and generate comprehensive report.
        Must be implemented by subclasses.

        Args:
            components: List of components to verify

        Returns:
            Complete verification report
        """
        pass