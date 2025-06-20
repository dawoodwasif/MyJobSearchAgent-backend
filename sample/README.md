# Sample Files for Testing

This folder should contain sample resume files for testing the GenApply API.

## Required Files

Add one or more of the following file types:
- `sample_resume.pdf` - A PDF resume file
- `sample_resume.docx` - A Word document resume
- `john_doe_resume.pdf` - Example resume in PDF format

## File Requirements

- **PDF files**: Should be text-based (not scanned images) for proper text extraction
- **Word files**: Should be in .docx format (newer Word format)
- **Content**: Should contain typical resume sections like education, work experience, skills, etc.

## Testing

Use the `test_api.py` script to test the API with these sample files:

```bash
python test_api.py
```

The script will automatically find and use resume files from this folder.
