"""
Utility functions for the API, such as document parsing and processing.
"""

# pylint: disable=import-error
import logging
import PyPDF2
import docx
from io import BytesIO

logger = logging.getLogger("AgentLogger")


def parse_document(file_content: bytes, file_type: str) -> str:
    """
    Parse document content and extract text.

    Args:
        file_content: Raw bytes of the uploaded file
        file_type: Type of document ('pdf', 'docx', 'txt')

    Returns:
        Extracted text from the document

    Raises:
        ValueError: If file type is not supported or parsing fails
    """
    try:
        if file_type.lower() == "pdf":
            return _parse_pdf(file_content)
        elif file_type.lower() == "docx":
            return _parse_docx(file_content)
        elif file_type.lower() in ["txt", "text"]:
            return _parse_text(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        error_msg = f"Error parsing {file_type} document: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def _parse_pdf(file_content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text_content = []

        # Try to extract text from all pages
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                if text and text.strip():
                    text_content.append(text)
            except Exception as page_error:
                logger.warning(
                    f"Could not extract text from page {page_num}: {str(page_error)}"
                )
                # Continue with next page instead of failing completely
                continue

        if not text_content:
            raise ValueError(
                "No text could be extracted from the PDF. The file may be image-based or corrupted."
            )

        extracted_text = "\n".join(text_content)
        logger.info(
            f"Successfully parsed PDF document ({len(extracted_text)} characters)"
        )
        return extracted_text
    except Exception as e:
        logger.error(f"PDF parsing failed: {str(e)}")
        raise


def _parse_docx(file_content: bytes) -> str:
    """Extract text from DOCX (Word) file."""
    try:
        docx_file = BytesIO(file_content)
        doc = docx.Document(docx_file)

        text_content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)

        extracted_text = "\n".join(text_content)
        logger.info(
            f"Successfully parsed DOCX document ({len(extracted_text)} characters)"
        )
        return extracted_text
    except Exception as e:
        logger.error(f"DOCX parsing failed: {str(e)}")
        raise


def _parse_text(file_content: bytes) -> str:
    """Extract text from plain text file."""
    try:
        extracted_text = file_content.decode("utf-8")
        logger.info(
            f"Successfully parsed text document ({len(extracted_text)} characters)"
        )
        return extracted_text
    except Exception as e:
        logger.error(f"Text parsing failed: {str(e)}")
        raise
