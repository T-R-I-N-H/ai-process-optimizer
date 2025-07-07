import io
from typing import Tuple
import logging

# Install these: pip install python-docx PyPDF2 lxml
try:
    import docx
except ImportError:
    docx = None
    logging.warning("python-docx not installed. DOCX parsing will not be available.")
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None
    logging.warning("PyPDF2 not installed. PDF parsing will not be available.")
try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None
    logging.warning("lxml or ElementTree not available. XML (BPMN) parsing might be limited.")


logger = logging.getLogger(__name__)

def parse_uploaded_file(filename: str, file_content: bytes) -> Tuple[str, str]:
    """
    Parses the content of an uploaded file (PDF, DOCX, BPMN XML) into plain text.

    Args:
        filename: The original filename (e.g., "my_process.pdf").
        file_content: The raw bytes content of the file.

    Returns:
        A tuple of (extracted_text, file_type).
        file_type will be 'pdf', 'docx', 'bpmn', or 'unknown'.
    """
    file_extension = filename.split('.')[-1].lower()
    extracted_text = ""
    file_type = "unknown"

    if file_extension == "pdf":
        file_type = "pdf"
        if PdfReader:
            try:
                pdf_reader = PdfReader(io.BytesIO(file_content))
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text() + "\n"
                logger.info(f"Successfully parsed PDF: {filename}")
            except Exception as e:
                logger.error(f"Error parsing PDF {filename}: {e}")
                extracted_text = f"Error parsing PDF: {e}"
        else:
            extracted_text = "PDF parsing library (PyPDF2) not available."
            logger.warning(extracted_text)

    elif file_extension == "docx":
        file_type = "docx"
        if docx:
            try:
                document = docx.Document(io.BytesIO(file_content))
                for paragraph in document.paragraphs:
                    extracted_text += paragraph.text + "\n"
                logger.info(f"Successfully parsed DOCX: {filename}")
            except Exception as e:
                logger.error(f"Error parsing DOCX {filename}: {e}")
                extracted_text = f"Error parsing DOCX: {e}"
        else:
            extracted_text = "DOCX parsing library (python-docx) not available."
            logger.warning(extracted_text)

    elif file_extension == "bpmn" or filename.endswith(".xml"): # BPMN is XML
        file_type = "bpmn"
        if ET:
            try:
                root = ET.fromstring(file_content.decode('utf-8'))
                # A very basic extraction for BPMN. For full detail, you'd parse specific BPMN elements.
                # This just gets all text content.
                for elem in root.iter():
                    if elem.text:
                        extracted_text += elem.text.strip() + "\n"
                logger.info(f"Successfully parsed BPMN/XML: {filename}")
            except Exception as e:
                logger.error(f"Error parsing BPMN/XML {filename}: {e}")
                extracted_text = f"Error parsing BPMN/XML: {e}"
        else:
            extracted_text = "XML parsing library (lxml/ElementTree) not available."
            logger.warning(extracted_text)

    else:
        file_type = "unknown"
        extracted_text = "Unsupported file type. Cannot extract text."
        logger.warning(f"Unsupported file type for {filename}. No text extracted.")

    return extracted_text.strip(), file_type