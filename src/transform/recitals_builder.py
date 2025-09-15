import re
from typing import List, Tuple

def parse_recitals_text(recitals_text: str) -> List[Tuple[int, str]]:
    """
    Parse recitals text into individual numbered recitals.

    Args:
        recitals_text: Raw text containing all recitals

    Returns:
        List of tuples (recital_number, recital_content)
    """
    recitals = []

    # Split by recital pattern (1), (2), etc.
    # Look for pattern like "(number)" at start of line or after whitespace
    recital_pattern = r'\n\s*\((\d+)\)\s*'

    # Split the text by recital numbers
    parts = re.split(recital_pattern, recitals_text)

    # Skip first part (before first recital) and process pairs
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            recital_num = int(parts[i])
            recital_content = parts[i + 1].strip()

            # Clean up content - remove extra whitespace and line breaks
            recital_content = ' '.join(recital_content.split())

            if recital_content:  # Only add non-empty recitals
                recitals.append((recital_num, recital_content))

    return recitals

def build_recitals_xml(recitals_text: str) -> str:
    """
    Build Akoma Ntoso XML structure for recitals.

    Args:
        recitals_text: Raw text containing all recitals

    Returns:
        XML string with proper recitals structure
    """
    recitals = parse_recitals_text(recitals_text)

    if not recitals:
        return "    <preamble>\n      <!-- No recitals found -->\n    </preamble>"

    xml_parts = ["    <preamble>", "      <recitals>"]

    for recital_num, content in recitals:
        xml_parts.extend([
            f'        <recital id="rec_{recital_num}">',
            f'          <num>({recital_num})</num>',
            f'          <p>{content}</p>',
            '        </recital>'
        ])

    xml_parts.extend(["      </recitals>", "    </preamble>"])

    return '\n'.join(xml_parts)

def get_recitals_summary(recitals_text: str) -> dict:
    """
    Get summary statistics about the recitals.

    Args:
        recitals_text: Raw text containing all recitals

    Returns:
        Dictionary with summary statistics
    """
    recitals = parse_recitals_text(recitals_text)

    if not recitals:
        return {
            "count": 0,
            "first_number": None,
            "last_number": None,
            "total_characters": 0
        }

    numbers = [num for num, _ in recitals]

    return {
        "count": len(recitals),
        "first_number": min(numbers),
        "last_number": max(numbers),
        "total_characters": sum(len(content) for _, content in recitals),
        "average_length": sum(len(content) for _, content in recitals) // len(recitals)
    }