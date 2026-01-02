"""PDF processing and LAQ data extraction using Docling and Mistral LLM."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import ollama
from docling.document_converter import DocumentConverter
from pydantic import BaseModel, Field, ValidationError

from app.services.config import Config


class QAPair(BaseModel):
    """Model for a question-answer pair."""

    question: str = Field(min_length=1, description="The question text")
    answer: str = Field(min_length=0, description="The answer text")


class LAQData(BaseModel):
    """Model for structured LAQ data."""

    pdf_title: str = Field("", description="Title of the LAQ document")
    laq_type: str = Field("", description="Type of LAQ (e.g., Starred, Unstarred)")
    laq_number: str = Field(description="LAQ identification number")
    minister: str = Field(description="Name of the minister")
    date: str = Field(description="Date of the LAQ")
    qa_pairs: List[QAPair] = Field(
        min_items=1, description="List of question-answer pairs"
    )
    mla_name: Optional[str] = Field(None, description="Person who tabled the question")
    attachments: List[str] = Field(default_factory=list, description="List of attachments")


class PDFProcessingError(Exception):
    """Raised when PDF processing fails."""

    pass


class PDFProcessor:
    """Handles PDF to structured LAQ data conversion."""

    def __init__(self, config: Config):
        """Initialize the PDF processor.

        Args:
            config: Application configuration
        """
        self.config = config
        self.converter = DocumentConverter()

    def extract_laq_number_from_filename(self, filename: str) -> Optional[str]:
        """Extract LAQ number from PDF filename.

        Handles various formats:
        - replylaqno.pdf -> extract the laq number after 'reply'
        - 123.pdf -> use the filename stem as LAQ number
        - laq_123.pdf -> extract number after common prefixes

        Args:
            filename: PDF filename

        Returns:
            Extracted LAQ number or None if not found
        """
        import re
        from pathlib import Path

        # Get filename without extension
        stem = Path(filename).stem.lower()

        # Pattern 1: replylaqno format (e.g., "reply123" -> "123")
        reply_match = re.search(r"reply(\d+[a-z]?)", stem, re.IGNORECASE)
        if reply_match:
            return reply_match.group(1).upper()

        # Pattern 2: Direct number at start (e.g., "123abc" -> "123ABC")
        number_match = re.match(r"^(\d+[a-z]?)", stem)
        if number_match:
            return number_match.group(1).upper()

        # Pattern 3: Common prefixes like laq_, laqno_, etc.
        prefix_match = re.search(
            r"(?:laq|laqno|question)[_-]?(\d+[a-z]?)", stem, re.IGNORECASE
        )
        if prefix_match:
            return prefix_match.group(1).upper()

        # Pattern 4: Any number in filename
        any_number = re.search(r"(\d+[a-z]?)", stem)
        if any_number:
            return any_number.group(1).upper()

        return None

    def validate_pdf_file(self, pdf_path: str) -> Path:
        """Validate that the file exists and is a PDF or Word document.

        Args:
            pdf_path: Path to the file

        Returns:
            Validated Path object

        Raises:
            PDFProcessingError: If validation fails
        """
        path = Path(pdf_path)

        if not path.exists():
            raise PDFProcessingError(f"File not found: {pdf_path}")

        if not path.is_file():
            raise PDFProcessingError(f"Not a file: {pdf_path}")

        # Accept PDF and Word documents
        allowed_exts = {'.pdf', '.doc', '.docx'}
        if path.suffix.lower() not in allowed_exts:
            raise PDFProcessingError(
                f"Unsupported file type: {pdf_path}\n"
                f"Expected one of: {', '.join(sorted(allowed_exts))}, got {path.suffix}"
            )

        # Check file size (warn if > 10MB)
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            print(
                f"⚠️ Large file detected ({size_mb:.1f} MB). Processing may take time."
            )

        return path

    def extract_markdown_from_pdf(
        self, pdf_path: Path, cache_result: bool = True
    ) -> str:
        """Convert PDF to markdown using Docling with optional caching.

        Args:
            pdf_path: Path to the PDF file
            cache_result: Whether to cache the conversion result

        Returns:
            Markdown content

        Raises:
            PDFProcessingError: If conversion fails
        """
        import hashlib
        from pathlib import Path

        # Check cache first if enabled
        if cache_result:
            cache_dir = Path("./cache/markdown")
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Generate cache key from file hash
            with open(pdf_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            cache_file = cache_dir / f"{pdf_path.stem}_{file_hash}.md"

            if cache_file.exists():
                print(f"✅ Using cached markdown conversion")
                return cache_file.read_text(encoding="utf-8")

        try:
            print(f"🔄 Converting PDF to markdown...")
            doc = self.converter.convert(str(pdf_path))
            markdown_data = doc.document.export_to_markdown()
            print(f"✅ Conversion successful ({len(markdown_data)} characters)")

            # Cache the result
            if cache_result:
                cache_file.write_text(markdown_data, encoding="utf-8")
                print(f"💾 Cached markdown conversion")

            return markdown_data
        except Exception as e:
            raise PDFProcessingError(f"Failed to convert PDF to markdown: {e}") from e

    def structure_laqs_with_mistral(
        self, markdown_data: str, pdf_path: Path
    ) -> LAQData:
        """Use Mistral LLM to extract structured LAQ data from markdown.

        Args:
            markdown_data: Markdown content from PDF
            pdf_path: Path to the original PDF file

        Returns:
            Validated LAQData object

        Raises:
            PDFProcessingError: If LLM processing or validation fails
        """
        try:
            print("🤖 Processing with Mistral LLM...")

            prompt = f"""
           You are a legal–legislative document analysis model.
Your task is to read the attached Legislative Assembly Question (LAQ) document
(PDF/DOC) and carefully analyze:
1. The questions raised by the MLA
2. The official replies given by the concerned Minister

The document may contain:
- Main questions and their reples.
- Adjacent questions may be Follow-up sub-questions that depend on earlier questions or an independent question.
- A single combined reply addressing multiple inter-related questions or multiple separate replies.

Follow-up questions are often linguistically dependent (e.g., “if so”, “thereof”,
“details”, “reasons”) and MUST NOT be treated as independent standalone questions.

You must semantically analyze question dependencies and reply coverage to preserve
meaning and intent.

After analysis, structure the extracted information in the EXACT JSON
format shown below.

--------------------------------------------------
REQUIRED JSON SCHEMA (STRICT – DO NOT MODIFY)
--------------------------------------------------
{{
  "laq_number": string | null,
  "mla_name": string | null,
  "type": string | null,
  "year": string | null,
  "date": string | null,
  "minister": string | null,
  "department": string | null,
  "demand_no": string | null,
  "cutmotion": boolean | null,
  "duplicate": boolean | null,
  "qa_pairs": [
    {{
      "question": string | null,
      "answer": string | null
    }}
  ],
  "attachments": [] | null
}}

--------------------------------------------------
ANALYSIS & EXTRACTION RULES
--------------------------------------------------

1. Identify whether the LAQ is STARRED or UNSTARRED from the document text.
2. Extract the LAQ number exactly as printed (alphanumeric if applicable).
3. Extract the full name of the MLA who tabled the question.
4. Extract the year from the document if available.
5. Extract the date of the question or reply exactly as stated.
6. Extract the name/designation of the Minister who answered the question.
7. Extract the Department, Demand No, Cut Motion status, and Duplicate status
   if present.
8. Detect all questions and sub-questions, including labels such as (a), (b), (c),
   numbered formats, or paragraph-style questions.
9. Identify follow-up questions using linguistic and semantic cues such as:
   - “if so”, “if yes”, “thereof”, “details of”, “reasons for”
   - references like “the above”, “the same”, “said proposal”
10. Determine logical dependency between questions and group inter-related
    questions conceptually during analysis.

--------------------------------------------------
QUESTION–ANSWER MAPPING LOGIC (CRITICAL)
--------------------------------------------------

11. Sometimes a SINGLE COMBINED REPLY answers multiple inter-related questions
    (main question + follow-up questions).
12. In such cases:
    - COPY THE SAME ANSWER TEXT for:
      • the main question
      • each dependent follow-up question
13. Do NOT fragment or paraphrase the combined reply differently for each question.
14. Ensure that every follow-up question inherits the contextual meaning of its
    main question.
15. If a reply indirectly or implicitly answers a question, map it correctly
    without inventing new information.
16. If a question exists but no reply is provided:
    - Set "answer" to an empty string.

--------------------------------------------------
ATTACHMENTS
--------------------------------------------------

17. If annexures or attachments are referenced (e.g., “Annexure-I”,
    “Annexure-II”), list them exactly in the "attachments" array.
18. If no attachments are mentioned, return an empty array or null.

--------------------------------------------------
STRICT OUTPUT CONSTRAINTS
--------------------------------------------------

- Output ONLY valid JSON.
- Do NOT include markdown, comments, or explanations.
- Do NOT infer or fabricate missing data.
- Do NOT change key names, nesting, or ordering.
- Ensure the JSON is fully parseable.
- Preserve semantic meaning across main and follow-up questions.

Begin analysis and extraction now.
{markdown_data[:self.config.markdown_chunk_size]}
"""

            response = ollama.generate(
                model=self.config.llm_model,
                prompt=prompt,
                stream=False,
                options={"timeout": self.config.ollama_timeout},
            )
            response_text = response["response"].strip()

            # Try to parse JSON
            try:
                laq_dict = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from response
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    laq_dict = json.loads(json_match.group())
                else:
                    raise PDFProcessingError(
                        f"Could not parse Mistral response as JSON.\n"
                        f"First 200 chars: {response_text[:200]}"
                    )

            # Validate with Pydantic
            try:
                laq_data = LAQData(**laq_dict)
                print(f"✅ Successfully extracted {len(laq_data.qa_pairs)} Q&A pairs")
                return laq_data
            except ValidationError as e:
                raise PDFProcessingError(f"Invalid LAQ data structure:\n{e}") from e

        except Exception as e:
            if isinstance(e, PDFProcessingError):
                raise
            raise PDFProcessingError(f"Mistral processing error: {e}") from e

    def process_pdf(self, pdf_path: str) -> LAQData:
        """Complete pipeline: validate -> extract LAQ number from filename -> structure with LLM.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Validated LAQData object

        Raises:
            PDFProcessingError: If any step fails
        """
        # Step 1: Validate
        validated_path = self.validate_pdf_file(pdf_path)

        # Step 2: Try to extract LAQ number from filename first
        filename_laq_number = self.extract_laq_number_from_filename(validated_path.name)
        if filename_laq_number:
            print(f"📄 Extracted LAQ number from filename: {filename_laq_number}")
        else:
            print("📄 No LAQ number found in filename, will use LLM extraction")

        # Step 3: Extract markdown
        markdown_data = self.extract_markdown_from_pdf(validated_path)

        # Step 4: Structure with LLM
        laq_data = self.structure_laqs_with_mistral(markdown_data, validated_path)

        # # Step 5: Override LAQ number with filename extraction if available
        # if filename_laq_number:
        #     print(
        #         f"🔄 Overriding LLM-extracted LAQ number '{laq_data.laq_number}' with filename-based '{filename_laq_number}'"
        #     )
        #     # Create new LAQData with filename-based LAQ number
        #     laq_data = LAQData(
        #         pdf_title=laq_data.pdf_title,
        #         laq_type=laq_data.laq_type,
        #         laq_number=filename_laq_number,  # Use filename-based number
        #         minister=laq_data.minister,
        #         date=laq_data.date,
        #         qa_pairs=laq_data.qa_pairs,
        #         tabled_by=laq_data.tabled_by,
        #         attachments=laq_data.attachments,
        #     )

        return laq_data
