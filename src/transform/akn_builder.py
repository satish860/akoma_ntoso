def create_akoma_ntoso_root() -> str:
    """
    Create the basic Akoma Ntoso root element structure.

    Returns:
        str: XML string with root element and namespace
    """
    return '''<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <!-- Document type element here -->
</akomaNtoso>'''