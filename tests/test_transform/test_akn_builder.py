import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.transform.akn_builder import create_akoma_ntoso_root

def test_create_akoma_ntoso_root():
    """Test creating the basic Akoma Ntoso root element"""
    xml = create_akoma_ntoso_root()

    # Basic assertions
    assert xml is not None, "Should return XML string"
    assert len(xml) > 0, "Should not be empty"
    assert '<akomaNtoso' in xml, "Should contain root element"
    assert 'xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"' in xml, "Should contain correct namespace"
    assert '</akomaNtoso>' in xml, "Should contain closing tag"

    print("Generated Akoma Ntoso root element:")
    print(xml)

if __name__ == "__main__":
    test_create_akoma_ntoso_root()
    print("Root element test passed!")