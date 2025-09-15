# Akoma Ntoso: Complete Guide

## What is Akoma Ntoso?

"Akoma Ntoso" means "linked hearts" in the Akan language of West Africa. It's an international XML standard (OASIS v1.0, approved 2018) for representing parliamentary, legislative, and judicial documents in a structured, machine-readable format.

## Core Philosophy

### "Everything has a name"
- Each meaningful part of a legal document gets a machine-readable XML tag
- Separates content from editorial additions
- Uses descriptive element names to precisely identify text segments

### Document-Centric Approach
- Focuses on the document's logical structure rather than visual presentation
- Preserves legal meaning while enabling digital processing
- Supports version tracking and temporal management

## Document Types Supported

### Legislative Documents
- **Acts**: Primary legislation (laws)
- **Bills**: Proposed legislation
- **Regulations**: Secondary legislation
- **Amendments**: Changes to existing legislation

### Parliamentary Documents
- **Debates**: Parliamentary proceedings
- **Questions**: Parliamentary questions and answers
- **Motions**: Formal proposals

### Judicial Documents
- **Judgments**: Court decisions
- **Court Reports**: Official court records

## XML Schema Structure

### Root Element
All Akoma Ntoso documents share the same root element:
```xml
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <!-- Document type element here -->
</akomaNtoso>
```

### Six Element Categories

#### 1. Hierarchies
Structural containers nested to arbitrary depth:
- `<part>`, `<chapter>`, `<section>`, `<article>`, `<paragraph>`
- Usually have `<num>` (numbering) and `<heading>` (title)
- Purpose: Give structural form, don't store content directly

```xml
<chapter eId="chp_1">
  <num>CHAPTER I</num>
  <heading>General provisions</heading>
  <section eId="sec_1">
    <num>Section 1</num>
    <heading>Definitions</heading>
    <!-- content goes in articles/paragraphs -->
  </section>
</chapter>
```

#### 2. Blocks
Containers of text or inline elements:
- `<p>` (paragraph), `<blockContainer>`, `<toc>` (table of contents)
- Follow mixed content model (text + inline elements)

```xml
<p eId="art_1__para_1">
  This regulation applies to <term>financial entities</term> as defined in Article 2.
</p>
```

#### 3. Inlines
Text fragments with special meaning:
- Semantic: `<term>`, `<def>`, `<ref>`, `<date>`
- Presentation: `<b>`, `<i>`, `<u>`

```xml
<p>The <term refersTo="#digitalResilience">digital operational resilience</term>
framework shall include <ref href="#art_5">Article 5</ref> requirements.</p>
```

#### 4. Markers
Content-less elements meaningful by position and attributes:
- `<noteRef>` (note references)
- `<eol>` (end of line)
- Metadata markers in `<meta>` section

#### 5. Containers
Organize document structures:
- `<body>`, `<preface>`, `<conclusions>`
- `<attachments>`, `<components>`

#### 6. Metadata Elements
Document metadata and ontological references:
- `<meta>` section with FRBR model
- `<identification>`, `<publication>`, `<classification>`

## Document Structure for Acts/Regulations

### Basic Structure
```xml
<akomaNtoso>
  <act name="DORA">
    <meta>
      <!-- Metadata section -->
    </meta>
    <preface>
      <!-- Title, preamble, recitals -->
    </preface>
    <body>
      <!-- Main content: chapters, articles -->
    </body>
    <conclusions>
      <!-- Final provisions -->
    </conclusions>
    <attachments>
      <!-- Annexes, schedules -->
    </attachments>
  </act>
</akomaNtoso>
```

### Metadata Section (FRBR Model)
Uses Functional Requirements for Bibliographic Records:

```xml
<meta>
  <identification source="#eu">
    <FRBRWork>
      <FRBRthis value="/eu/act/2022/reg-2554"/>
      <FRBRuri value="/eu/act/2022/reg-2554"/>
      <FRBRdate date="2022-12-14" name="enacted"/>
      <FRBRauthor href="#eu"/>
      <FRBRcountry value="eu"/>
      <FRBRnumber value="2554"/>
      <FRBRname value="Digital Operational Resilience Act"/>
    </FRBRWork>
    <FRBRExpression>
      <FRBRthis value="/eu/act/2022/reg-2554/eng"/>
      <FRBRuri value="/eu/act/2022/reg-2554/eng"/>
      <FRBRdate date="2022-12-14" name="enacted"/>
      <FRBRauthor href="#eu"/>
      <FRBRlanguage language="eng"/>
    </FRBRExpression>
    <FRBRManifestation>
      <FRBRthis value="/eu/act/2022/reg-2554/eng/xml"/>
      <FRBRuri value="/eu/act/2022/reg-2554/eng/xml"/>
      <FRBRdate date="2025-01-17" name="application"/>
      <FRBRauthor href="#eu"/>
      <FRBRformat value="xml"/>
    </FRBRManifestation>
  </identification>
</meta>
```

### Article Structure Example
```xml
<article eId="art_1">
  <num>Article 1</num>
  <heading>Subject matter</heading>
  <paragraph eId="art_1__para_1">
    <num>1.</num>
    <content>
      <p>This Regulation lays down uniform requirements concerning:</p>
      <blockList eId="art_1__para_1__list_1">
        <item eId="art_1__para_1__list_1__item_a">
          <num>(a)</num>
          <p>information and communication technology risk management;</p>
        </item>
        <item eId="art_1__para_1__list_1__item_b">
          <num>(b)</num>
          <p>reporting of major ICT-related incidents;</p>
        </item>
      </blockList>
    </content>
  </paragraph>
</article>
```

## Important Attributes

### eId (Element Identifier)
- Unique identifier for each structural element
- Used for cross-referencing
- Format: hierarchical (e.g., `art_1__para_2__list_1__item_a`)

### wId (Work Identifier)
- Identifies the "work" level in FRBR model
- Used for amendments and versions

### refersTo
- Points to ontological concepts
- Links text to external vocabularies

## Common Patterns in Legal Documents

### Numbering Schemes
- **Articles**: "Article 1", "Art. 2"
- **Paragraphs**: "1.", "2.", "(1)", "(2)"
- **Sub-items**: "(a)", "(b)", "(c)" or "i)", "ii)", "iii)"

### Cross-References
```xml
<p>As provided in <ref href="#art_5">Article 5</ref> and
<ref href="#chp_2">Chapter II</ref>...</p>
```

### Definitions
```xml
<article eId="art_3">
  <heading>Definitions</heading>
  <paragraph eId="art_3__para_1">
    <content>
      <p>For the purposes of this Regulation:</p>
      <blockList>
        <item eId="art_3__para_1__point_1">
          <num>(1)</num>
          <p><def>'digital operational resilience'</def> means the ability of a financial entity to...</p>
        </item>
      </blockList>
    </content>
  </paragraph>
</article>
```

## Implementation Strategy for Parser

### Phase 1: Basic Structure Detection
1. Extract text from PDF
2. Identify document title and type
3. Find chapter boundaries (regex: `CHAPTER [IVX]+|Chapter \d+`)
4. Find article boundaries (regex: `Article \d+`)
5. Extract article titles

### Phase 2: Hierarchical Parsing
1. Parse paragraphs within articles (numbered: `\d+\.` or `\(\d+\)`)
2. Identify sub-items (letters: `\([a-z]\)`, romans: `\([ivx]+\)`)
3. Build parent-child relationships
4. Handle cross-references

### Phase 3: Metadata Extraction
1. Extract document information (title, date, authority)
2. Generate FRBR metadata
3. Create eId scheme
4. Add proper namespaces

### Phase 4: XML Generation
1. Build XML tree using lxml
2. Apply Akoma Ntoso schema structure
3. Validate against official schema
4. Output formatted XML

## Tools and Libraries

### XML Processing
- **lxml**: XML generation and validation
- **xmlschema**: Schema validation
- **BeautifulSoup**: Alternative XML parsing

### Text Processing
- **regex**: Advanced pattern matching
- **spaCy**: Natural language processing
- **nltk**: Text processing utilities

### PDF Processing
- **pdfplumber**: Text extraction with layout info
- **PyPDF2**: Basic PDF reading
- **pdfminer**: Advanced PDF analysis

## Validation and Quality

### Schema Validation
- Validate against official Akoma Ntoso XSD
- Check eId uniqueness and consistency
- Verify required elements are present

### Content Quality
- Ensure all text is captured
- Verify structure matches original
- Check cross-references are valid
- Validate metadata completeness

## Common Challenges

### PDF Extraction Issues
- Multi-column layouts
- Headers/footers interference
- Table extraction
- Formatting artifacts

### Structure Detection
- Inconsistent numbering schemes
- Nested lists complexity
- Cross-page elements
- Footnotes and annotations

### Metadata Generation
- Date format variations
- Authority identification
- Language detection
- Classification schemes

## Best Practices

### Design Principles
1. **Fail gracefully**: Handle malformed input
2. **Preserve structure**: Maintain legal document integrity
3. **Enable round-trip**: Allow regeneration of original structure
4. **Support validation**: Include quality checks
5. **Document decisions**: Log parsing choices for review

### Performance Considerations
1. **Stream processing**: Handle large documents efficiently
2. **Incremental parsing**: Process documents in chunks
3. **Caching**: Store intermediate results
4. **Parallel processing**: Handle multiple documents concurrently

This guide provides the foundation for implementing an Akoma Ntoso parser that can convert PDF legal documents into structured, machine-readable XML format.