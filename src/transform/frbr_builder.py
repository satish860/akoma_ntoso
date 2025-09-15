from .models import DocumentMetadata

def build_frbr_metadata(metadata: DocumentMetadata) -> str:
    """Convert validated metadata to FRBR XML structure for Akoma Ntoso"""

    # Build URIs from metadata
    # Convert document type to short form for URIs
    doc_type_map = {
        "regulation": "reg",
        "act": "act",
        "directive": "dir",
        "implementing regulation": "impl-reg",
        "delegated regulation": "del-reg"
    }

    doc_type_short = doc_type_map.get(metadata.document_type.lower(), "doc")

    # Build hierarchical URIs
    # Example: /eu/reg/2022-2554
    number_safe = metadata.number.replace("/", "-")
    work_uri = f"/{metadata.country}/{doc_type_short}/{number_safe}"
    expression_uri = f"{work_uri}/{metadata.language}"
    manifestation_uri = f"{expression_uri}/xml"

    # Use published date if available, otherwise enacted date
    publication_date = metadata.date_published or metadata.date_enacted

    return f'''<meta>
  <identification source="#{metadata.country}">
    <FRBRWork>
      <FRBRthis value="{work_uri}"/>
      <FRBRuri value="{work_uri}"/>
      <FRBRdate date="{metadata.date_enacted}" name="enacted"/>
      <FRBRauthor href="#{metadata.country}"/>
      <FRBRcountry value="{metadata.country}"/>
      <FRBRnumber value="{metadata.number}"/>
      <FRBRname value="{metadata.title}"/>
    </FRBRWork>
    <FRBRExpression>
      <FRBRthis value="{expression_uri}"/>
      <FRBRuri value="{expression_uri}"/>
      <FRBRdate date="{metadata.date_enacted}" name="enacted"/>
      <FRBRauthor href="#{metadata.country}"/>
      <FRBRlanguage language="{metadata.language}"/>
    </FRBRExpression>
    <FRBRManifestation>
      <FRBRthis value="{manifestation_uri}"/>
      <FRBRuri value="{manifestation_uri}"/>
      <FRBRdate date="{publication_date}" name="publication"/>
      <FRBRauthor href="#{metadata.country}"/>
      <FRBRformat value="xml"/>
    </FRBRManifestation>
  </identification>
</meta>'''