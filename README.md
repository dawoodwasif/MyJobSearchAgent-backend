# GenApply API Documentation

## Overview
RESTful API for resume processing, cover letter generation, and resume optimization using AI.

## Setup
```bash
pip install -r requirements.txt
python app.py
```

## Endpoints

### 1. Extract Resume JSON
**POST** `/api/extract-resume-json`

Extract structured JSON from resume PDF/DOCX files.

**Form Data:**
- `file`: Resume file (PDF/DOCX)
- `api_key`: OpenAI/Gemini API key
- `model_type`: "OpenAI" or "Gemini" (optional, default: "OpenAI")
- `model`: Model name (optional, default: "gpt-4o")

**Response:**
```json
{
  "success": true,
  "resume_json": {...},
  "extracted_text_length": 1234
}
```

### 2. Generate Cover Letter
**POST** `/api/generate-cover-letter`

Generate personalized cover letter PDF.

**JSON Body:**
```json
{
  "resume_json": {...},
  "job_description": "...",
  "position": "Software Engineer",
  "company_name": "Tech Corp",
  "location": "San Francisco, CA",
  "personal_info": {
    "name": "John Doe",
    "phone": "555-1234",
    "email": "john@email.com"
  },
  "api_key": "your-api-key",
  "model_type": "OpenAI",
  "model": "gpt-4o"
}
```

**Response:** PDF file download

### 3. Optimize Resume
**POST** `/api/optimize-resume`

Generate optimized resume PDF based on job description.

**JSON Body:**
```json
{
  "resume_json": {...},
  "job_description": "...",
  "template": "Modern",
  "api_key": "your-api-key",
  "model_type": "OpenAI",
  "model": "gpt-4o",
  "section_ordering": ["education", "work", "skills", "projects", "awards"],
  "improve_resume": true
}
```

**Response:** PDF file download

### 4. Get Templates
**GET** `/api/templates`

Get available resume templates.

**Response:**
```json
{
  "templates": ["Simple", "Modern", "Awesome", ...],
  "template_info": {...}
}
```

### 5. Health Check
**GET** `/api/health`

Check API status.

## Error Handling
All errors return JSON with error message and HTTP status code.

```json
{
  "error": "Error description",
  "traceback": "..." // Only in debug mode
}
```

## Usage Examples

### cURL Examples
```bash
# Extract resume JSON
curl -X POST http://localhost:5000/api/extract-resume-json \
  -F "file=@resume.pdf" \
  -F "api_key=your-key"

# Generate cover letter
curl -X POST http://localhost:5000/api/generate-cover-letter \
  -H "Content-Type: application/json" \
  -d '{"resume_json": {...}, "job_description": "...", ...}'
```
