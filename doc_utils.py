from pdfminer.high_level import extract_text
import docx2txt
import tempfile
import os
from io import BytesIO


def extract_text_from_pdf(file):
    """Extract text from PDF file or FileStorage object"""
    if hasattr(file, "read"):
        # It's a file-like object (FileStorage) - create BytesIO object
        file.seek(0)  # Reset file pointer
        file_content = file.read()
        return extract_text(BytesIO(file_content))
    else:
        # It's a file path
        return extract_text(file)


def extract_text_from_docx(file):
    """Extract text from DOCX file or FileStorage object"""
    if hasattr(file, "read"):
        # It's a file-like object (FileStorage) - save to temp file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            file.seek(0)  # Reset file pointer
            temp_file.write(file.read())
            temp_file_path = temp_file.name

        try:
            text = docx2txt.process(temp_file_path)
            return text
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
    else:
        # It's a file path
        return docx2txt.process(file)


def get_file_type(file):
    """Determine file type from content_type and filename"""
    # Try to get content_type (for Flask FileStorage objects)
    content_type = getattr(file, "content_type", None)
    filename = getattr(file, "filename", "")

    # Check content type first
    if content_type == "application/pdf":
        return "pdf"
    elif content_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        return "docx"
    elif content_type == "application/msword":
        return "doc"
    elif content_type == "application/json":
        return "json"
    elif content_type and content_type.startswith("text/"):
        return "text"

    # Fallback to filename extension
    if filename:
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            return "pdf"
        elif filename_lower.endswith(".docx"):
            return "docx"
        elif filename_lower.endswith(".doc"):
            return "doc"
        elif filename_lower.endswith(".json"):
            return "json"
        elif filename_lower.endswith((".txt", ".text")):
            return "text"

    return "unknown"


def extract_text_from_upload(file):
    file_type = get_file_type(file)

    try:
        if file_type == "pdf":
            text = extract_text_from_pdf(file)
            return text
        elif file_type in ["docx", "doc"]:
            text = extract_text_from_docx(file)
            return text
        elif file_type == "json":
            file.seek(0)  # Reset file pointer
            return file.read().decode("utf-8")
        elif file_type == "text":
            file.seek(0)  # Reset file pointer
            return file.read().decode("utf-8")
        else:
            # Try to decode as text as a last resort
            try:
                file.seek(0)  # Reset file pointer
                return file.read().decode("utf-8")
            except Exception as decode_error:
                raise ValueError(
                    f"Unsupported file type or unable to extract text. File type detected: {file_type}, Content-Type: {getattr(file, 'content_type', 'unknown')}, Filename: {getattr(file, 'filename', 'unknown')}, Decode error: {str(decode_error)}"
                )
    except Exception as e:
        raise ValueError(
            f"Error processing file: {str(e)}. File type: {file_type}, Content-Type: {getattr(file, 'content_type', 'unknown')}, Filename: {getattr(file, 'filename', 'unknown')}"
        )


def escape_for_latex(data):
    if isinstance(data, dict):
        new_data = {}
        for key in data.keys():
            new_data[key] = escape_for_latex(data[key])
        return new_data
    elif isinstance(data, list):
        return [escape_for_latex(item) for item in data]
    elif isinstance(data, str):
        # Adapted from https://stackoverflow.com/q/16259923
        latex_special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\^{}",
            "\\": r"\textbackslash{}",
            "\n": "\\newline%\n",
            "-": r"{-}",
            "\xA0": "~",  # Non-breaking space
            "[": r"{[}",
            "]": r"{]}",
        }
        return "".join([latex_special_chars.get(c, c) for c in data])

    return data
