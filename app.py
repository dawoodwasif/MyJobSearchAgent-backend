from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
from io import BytesIO
import traceback

# Import existing utilities
from doc_utils import extract_text_from_upload, escape_for_latex
from prompt_engineering import generate_json_resume, tailor_resume
from templates import generate_latex, template_commands
from render import render_latex, render_cover_letter

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Directory to store resume JSON files
RESUME_STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'resume_storage')
os.makedirs(RESUME_STORAGE_DIR, exist_ok=True)


@app.route("/")
def home():
    return "Hello, Flask is live on Render!"

def save_resume_data(file_id, resume_json):
    """Save resume JSON data to file"""
    try:
        file_path = os.path.join(RESUME_STORAGE_DIR, f"{file_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(resume_json, f, indent=2, ensure_ascii=False)
        # Minimal debug
        print(f"Saved resume data to file: {file_path}")
        return True
    except Exception as e:
        print(f"Failed to save resume data for file_id {file_id}: {str(e)}")
        return False

def get_resume_data(file_id):
    """Get resume JSON data from file"""
    try:
        file_path = os.path.join(RESUME_STORAGE_DIR, f"{file_id}.json")
        if not os.path.exists(file_path):
            print(f"Resume file not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            resume_json = json.load(f)
        # Minimal debug
        print(f"Retrieved resume data from file: {file_path}")
        return resume_json
    except Exception as e:
        print(f"Failed to load resume data for file_id {file_id}: {str(e)}")
        return None

def cleanup_old_files():
    """Clean up old resume files (optional - can be called periodically)"""
    try:
        import time
        current_time = time.time()
        max_age = 24 * 3600  # 24 hours in seconds
        
        for filename in os.listdir(RESUME_STORAGE_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(RESUME_STORAGE_DIR, filename)
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age:
                    os.remove(file_path)
                    print(f"Cleaned up old file: {file_path}")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

# Template for cover letter with comprehensive personal information
COVER_LETTER_TEMPLATE = r"""
\documentclass[11pt,a4paper,roman]{moderncv}      
\usepackage[english]{babel}

\moderncvstyle{classic}                            
\moderncvcolor{green}                            

% character encoding
\usepackage[utf8]{inputenc}                     

% adjust the page margins
\usepackage[scale=0.75]{geometry}

% personal data
\name{{{NAME_FIRST}}}{{{NAME_LAST}}}
\phone[mobile]{{{PHONE}}}               
\email{{{EMAIL}}}{ADDRESS_SECTION}{LINKEDIN_SECTION}

\begin{document}

\recipient{{{RECIPIENT_NAME}}}{{
{COMPANY_NAME}{DEPARTMENT_SECTION}\\
{LOCATION}
}}

\date{{\today}}
\opening{{{OPENING_GREETING}}}
\closing{{Sincerely,}}

\makelettertitle

{BODY_CONTENT}

\vspace{0.5cm}

\makeletterclosing

\end{document}
"""

def generate_cover_letter_content(api_key, job_description, position, company_name, location, resume_info, model="gpt-4o", model_type="OpenAI"):
    """Generate cover letter content using AI"""
    # Minimal debug
    print(f"Generating cover letter content with model_type={model_type}, model={model}")
    from openai import OpenAI
    
    prompt = f"""
    Write a professional cover letter for the following job details:
    - Job Title: {position}
    - Company Name: {company_name}
    - Location: {location}
    - Job Description: {job_description}

    Use the following resume information: {resume_info}

    Generate only 3 paragraphs of content (no salutations, no closing). Each paragraph should be complete sentences ending with periods.
    """
    
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in writing professional cover letters."},
                {"role": "user", "content": prompt},
            ],
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        raise Exception(f"OpenAI API error: {str(e)}")

@app.route('/api/extract-resume-json', methods=['POST'])
def extract_resume_json():
    """Extract JSON structure from uploaded resume PDF/DOCX"""
    import traceback
    try:
        # Minimal debug
        print("extract_resume_json called")
        # Get file_id for request tracking
        file_id = request.form.get('file_id', 'unknown')
        
        # Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded", "file_id": file_id}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected", "file_id": file_id}), 400
        
        # Get API parameters
        api_key = request.form.get('api_key')
        model_type = request.form.get('model_type', 'OpenAI')
        model = request.form.get('model', 'gpt-4o')
        
        if not api_key:
            return jsonify({"error": "API key is required", "file_id": file_id}), 400
        
        # Extract text from file
        try:
            text = extract_text_from_upload(file)
        except Exception as text_error:
            return jsonify({
                "error": f"Failed to extract text from file: {str(text_error)}",
                "traceback": traceback.format_exc(),
                "file_id": file_id
            }), 500
        
        if len(text.strip()) < 50:
            return jsonify({"error": "Extracted text is too short. Please check the file.", "file_id": file_id}), 400
        
        # Generate JSON resume
        try:
            from prompt_engineering import generate_json_resume
            json_resume = generate_json_resume(text, api_key, model, model_type)
            # Minimal debug
            print(f"JSON resume generated for file_id: {file_id}")
            
            # Validate that we have some content
            if not json_resume or (isinstance(json_resume, dict) and len(json_resume) == 0):
                return jsonify({
                    "error": "Generated resume JSON is empty. Please check your API key and try again.",
                    "extracted_text_length": len(text),
                    "resume_json": {},
                    "file_id": file_id
                }), 500
            
        except Exception as json_error:
            return jsonify({
                "error": f"Failed to generate JSON resume: {str(json_error)}",
                "traceback": traceback.format_exc(),
                "extracted_text_length": len(text),
                "file_id": file_id
            }), 500
        
        response_data = {
            "success": True,
            "resume_json": json_resume,
            "extracted_text_length": len(text),
            "file_id": file_id
        }
        
        # Save resume data to file
        save_resume_data(file_id, json_resume)
        
        return jsonify(response_data)
        
    except Exception as e:
        file_id = request.form.get('file_id', 'unknown')
        return jsonify({
            "error": f"Failed to extract resume JSON: {str(e)}",
            "traceback": traceback.format_exc(),
            "file_id": file_id
        }), 500

@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover_letter_api():
    """Generate cover letter from file_id OR resume_json and job description"""
    try:
        # Minimal debug
        print("generate_cover_letter_api called")
        data = request.get_json()
        # Get file_id for request tracking
        file_id = data.get('file_id', 'unknown') if data else 'unknown'
        
        # Support both old format (with resume_json) and new format (file_id only)
        resume_json = data.get('resume_json')
        if resume_json:
            save_resume_data(file_id, resume_json)
        else:
            # New format: load from file_id
            required_fields = ['file_id', 'job_description', 'api_key']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}", "file_id": file_id}), 400
            resume_json = get_resume_data(file_id)
            if resume_json is None:
                return jsonify({"error": "Resume data not found. Please re-upload your resume.", "file_id": file_id}), 404
        
        # Common required fields
        required_common = ['job_description', 'api_key']
        missing_common = [field for field in required_common if field not in data]
        if missing_common:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_common)}", "file_id": file_id}), 400
        job_description = data['job_description']
        api_key = data['api_key']
        model_type = data.get('model_type', 'OpenAI')
        model = data.get('model', 'gpt-4o')
        include_additional_personal_info = data.get('include_additional_personal_info', False)
        
        # Extract personal information with intelligent fallbacks
        personal_info = data.get('personal_info', {})
        if not personal_info or not any([personal_info.get('name'), personal_info.get('email'), personal_info.get('phone')]):
            if resume_json:
                # Extract from personal section
                resume_personal = resume_json.get('personal', {})
                if not personal_info.get('name') and resume_personal.get('name'):
                    personal_info['name'] = resume_personal['name']
                if not personal_info.get('email') and resume_personal.get('email'):
                    personal_info['email'] = resume_personal['email']
                if not personal_info.get('phone') and resume_personal.get('phone'):
                    personal_info['phone'] = resume_personal['phone']
                if not personal_info.get('address') and resume_personal.get('address'):
                    personal_info['address'] = resume_personal['address']
                if not personal_info.get('linkedin') and resume_personal.get('linkedin'):
                    personal_info['linkedin'] = resume_personal['linkedin']
        
        # Apply defaults for missing personal info
        personal_info = {
            'name': personal_info.get('name', 'John Doe').strip(),
            'phone': personal_info.get('phone', '+1 (555) 123-4567').strip(),
            'email': personal_info.get('email', 'example@email.com').strip(),
            'address': personal_info.get('address', '').strip(),
            'linkedin': personal_info.get('linkedin', '').strip()
        }
        
        # Extract company information with intelligent fallbacks
        company_info = data.get('company_info', {})
        position = data.get('position') or company_info.get('position', 'Software Engineer')
        company_name = company_info.get('company_name') or data.get('company_name', 'Hiring Company')
        location = company_info.get('location') or data.get('location', 'Location')
        hiring_manager = company_info.get('hiring_manager') or data.get('hiring_manager', '')
        department = company_info.get('department') or data.get('department', '')
        
        # Consolidate company info
        company_info = {
            'position': position,
            'company_name': company_name,
            'location': location,
            'hiring_manager': hiring_manager,
            'department': department
        }
        
        resume_info = json.dumps(resume_json, indent=2)
        
        body_content = generate_cover_letter_content(
            api_key, job_description, position, company_name, location, resume_info, model, model_type
        )
        
        name_parts = personal_info['name'].strip().split()
        if len(name_parts) == 0:
            name_parts = ['John', 'Doe']
        elif len(name_parts) == 1:
            name_parts.append('Doe')
        
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        def safe_latex_escape(text, default=""):
            if not text or str(text).strip() == "":
                return default
            text = str(text).strip()
            latex_chars = {
                '\\': '\\textbackslash{}',
                '{': '\\{',
                '}': '\\}',
                '$': '\\$',
                '&': '\\&',
                '%': '\\%',
                '#': '\\#',
                '^': '\\textasciicircum{}',
                '_': '\\_',
                '~': '\\textasciitilde{}',
                '<': '\\textless{}',
                '>': '\\textgreater{}',
                '|': '\\textbar{}'
            }
            for char, replacement in latex_chars.items():
                text = text.replace(char, replacement)
            return text
        
        # Validate and enhance body content
        if not body_content or body_content.strip() == "":
            body_content = f"I am writing to express my strong interest in the {position} position at {company_name}. Thank you for considering my application."
        # Build optional sections based on flag
        address_section = ""
        if include_additional_personal_info and personal_info['address']:
            address_section = f"\n\\address{{{safe_latex_escape(personal_info['address'])}}}"
        
        linkedin_section = ""
        if include_additional_personal_info and personal_info['linkedin']:
            linkedin_section = f"\n\\homepage{{{safe_latex_escape(personal_info['linkedin'])}}}"
        
        department_section = ""
        if department:
            department_section = f"\\\\{safe_latex_escape(department)}"
        
        # Determine recipient and greeting
        recipient_name = "Hiring Manager"
        opening_greeting = "Dear Hiring Manager,"
        
        if hiring_manager and hiring_manager.strip():
            recipient_name = safe_latex_escape(hiring_manager.strip())
            # Simple name check for greeting
            if hiring_manager.strip().lower() not in ['hiring manager', 'hr team', 'recruitment team']:
                opening_greeting = f"Dear {recipient_name},"
        
        import re
        latex_content = COVER_LETTER_TEMPLATE.replace("{COMPANY_NAME}", safe_latex_escape(company_name, "Hiring Company"))
        latex_content = latex_content.replace("{LOCATION}", safe_latex_escape(location, "Location"))
        latex_content = latex_content.replace("{BODY_CONTENT}", safe_latex_escape(body_content))
        latex_content = latex_content.replace("{NAME_FIRST}", safe_latex_escape(first_name, "John"))
        latex_content = latex_content.replace("{NAME_LAST}", safe_latex_escape(last_name, "Doe"))
        latex_content = latex_content.replace("{PHONE}", safe_latex_escape(personal_info['phone'], "+1 (555) 123-4567"))
        latex_content = latex_content.replace("{EMAIL}", safe_latex_escape(personal_info['email'], "example@email.com"))
        latex_content = latex_content.replace("{ADDRESS_SECTION}", address_section)
        latex_content = latex_content.replace("{LINKEDIN_SECTION}", linkedin_section)
        latex_content = latex_content.replace("{DEPARTMENT_SECTION}", department_section)
        latex_content = latex_content.replace("{RECIPIENT_NAME}", recipient_name)
        latex_content = latex_content.replace("{OPENING_GREETING}", opening_greeting)
        latex_content = latex_content.replace("{{}}", "")
        latex_content = latex_content.replace("\\\\\\\\", "\\\\")  # Remove double line breaks
        latex_content = re.sub(r'\\(vspace|hspace|textwidth|linewidth)\{\{([^}]+)\}\}', r'\\\1{\2}', latex_content)
        latex_content = re.sub(r'\{\{([^{}]+)\}\}', r'{\1}', latex_content)
        
        pdf_bytes = render_cover_letter(["pdflatex", "cover_letter.tex"], latex_content, "cover_letter.pdf")
        
        if pdf_bytes:
            return send_file(
                BytesIO(pdf_bytes),
                as_attachment=True,
                download_name=f"cover_letter_{file_id}.pdf",
                mimetype="application/pdf"
            )
        else:
            return jsonify({"error": "Failed to generate PDF", "file_id": file_id}), 500
            
    except Exception as e:
        file_id = data.get('file_id', 'unknown') if 'data' in locals() and data else 'unknown'
        return jsonify({
            "error": f"Failed to generate cover letter: {str(e)}",
            "traceback": traceback.format_exc(),
            "file_id": file_id
        }), 500

@app.route('/api/optimize-resume', methods=['POST'])
def optimize_resume():
    """Generate optimized resume from file_id OR resume_json, job description, and template preference"""
    try:
        # Minimal debug
        print("optimize_resume called")
        data = request.get_json()
        file_id = data.get('file_id', 'unknown') if data else 'unknown'
        resume_json = data.get('resume_json')
        if resume_json:
            save_resume_data(file_id, resume_json)
        else:
            required_fields = ['file_id', 'job_description', 'template', 'api_key']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}", "file_id": file_id}), 400
            resume_json = get_resume_data(file_id)
            if resume_json is None:
                return jsonify({"error": "Resume data not found. Please re-upload your resume.", "file_id": file_id}), 404
        
        if not all([data.get('job_description'), data.get('template'), data.get('api_key')]):
            missing = []
            if not data.get('job_description'): missing.append('job_description')
            if not data.get('template'): missing.append('template')
            if not data.get('api_key'): missing.append('api_key')
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}", "file_id": file_id}), 400
        
        job_description = data['job_description']
        template = data['template']
        api_key = data['api_key']
        model_type = data.get('model_type', 'OpenAI')
        model = data.get('model', 'gpt-4o')
        section_ordering = data.get('section_ordering', ['education', 'work', 'skills', 'projects', 'awards'])
        improve_resume = data.get('improve_resume', True)
        
        if template not in template_commands:
            return jsonify({"error": f"Invalid template. Available templates: {list(template_commands.keys())}", "file_id": file_id}), 400
        
        resume_text = json.dumps(resume_json, indent=2)
        combined_text = f"{resume_text}\n\nOptimize this resume for the following job:\n{job_description}"
        
        if improve_resume:
            optimized_text = tailor_resume(combined_text, api_key, model, model_type)
            optimized_json = generate_json_resume(optimized_text, api_key, model, model_type)
        else:
            optimized_json = resume_json
        
        latex_resume = generate_latex(template, optimized_json, section_ordering)
        resume_bytes = render_latex(template_commands[template], latex_resume)
        
        if resume_bytes:
            return send_file(
                BytesIO(resume_bytes),
                as_attachment=True,
                download_name=f"optimized_resume_{file_id}.pdf",
                mimetype="application/pdf"
            )
        else:
            return jsonify({"error": "Failed to generate PDF", "file_id": file_id}), 500
        
    except Exception as e:
        file_id = data.get('file_id', 'unknown') if 'data' in locals() and data else 'unknown'
        return jsonify({
            "error": f"Failed to optimize resume: {str(e)}",
            "traceback": traceback.format_exc(),
            "file_id": file_id
        }), 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get available resume templates"""
    templates_list = list(template_commands.keys())
    response_data = {
        "templates": templates_list,
        "template_info": {
            "Simple": "Basic single-column layout",
            "Modern": "Clean modern design with color accents",
            "Awesome": "Professional two-column layout",
            "Deedy": "Two-column design with emphasis on skills",
            "BGJC": "Traditional academic style",
            "Plush": "Elegant two-column with modern typography",
            "Alta": "Contemporary design with subtle colors"
        }
    }
    return jsonify(response_data)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    response_data = {
        "status": "healthy",
        "message": "GenApply API is running",
        "endpoints": [
            "/api/extract-resume-json",
            "/api/generate-cover-letter", 
            "/api/optimize-resume",
            "/api/ai-enhance",
            "/api/templates"
        ]
    }
    return jsonify(response_data)

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.route('/api/ai-enhance', methods=['POST'])
def ai_enhance():
    """AI Enhancement API - analyze resume against job description and provide optimized content"""
    try:
        # Minimal debug
        print("ai_enhance called")
        if request.content_type and 'multipart/form-data' in request.content_type:
            file_id = request.form.get('file_id', 'unknown')
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded", "file_id": file_id}), 400
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected", "file_id": file_id}), 400
            job_description = request.form.get('job_description', '')
            api_key = request.form.get('api_key')
            model_type = request.form.get('model_type', 'OpenAI')
            model = request.form.get('model', 'gpt-4o')
            text = extract_text_from_upload(file)
            resume_json = generate_json_resume(text, api_key, model, model_type)
        else:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided", "file_id": "unknown"}), 400
            file_id = data.get('file_id', 'unknown')
            resume_json = data.get('resume_json')
            if not resume_json and file_id != 'unknown':
                resume_json = get_resume_data(file_id)
                if resume_json is None:
                    return jsonify({"error": "Resume data not found. Please provide resume_json or re-upload your resume.", "file_id": file_id}), 404
            job_description = data.get('job_description', '')
            api_key = data.get('api_key')
            model_type = data.get('model_type', 'OpenAI')
            model = data.get('model', 'gpt-4o')
        
        if not all([resume_json, job_description, api_key]):
            missing = []
            if not resume_json: missing.append('resume_json')
            if not job_description: missing.append('job_description')
            if not api_key: missing.append('api_key')
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}", "file_id": file_id}), 400
        
        enhancement_result = generate_ai_enhancement(resume_json, job_description, api_key, model, model_type)
        enhancement_result['file_id'] = file_id
        return jsonify(enhancement_result)
        
    except Exception as e:
        file_id = 'unknown'
        if request.content_type and 'multipart/form-data' in request.content_type:
            file_id = request.form.get('file_id', 'unknown')
        elif request.get_json():
            file_id = request.get_json().get('file_id', 'unknown')
        return jsonify({
            "error": f"Failed to enhance resume: {str(e)}",
            "traceback": traceback.format_exc(),
            "file_id": file_id
        }), 500

def generate_ai_enhancement(resume_json, job_description, api_key, model="gpt-4o", model_type="OpenAI"):
    """Generate AI-powered enhancement analysis and content"""
    from openai import OpenAI
    resume_text = json.dumps(resume_json, indent=2)
    analysis_prompt = f"""
    Analyze the following resume against the job description and provide a comprehensive assessment.
    
    RESUME:
    {resume_text}
    
    JOB DESCRIPTION:
    {job_description}
    
    Provide your analysis in the following JSON format:
    {{
        "match_score": <0-100 integer>,
        "strengths": ["strength1", "strength2", "strength3"],
        "gaps": ["gap1", "gap2", "gap3"],
        "suggestions": ["suggestion1", "suggestion2", "suggestion3"],
        "keyword_analysis": {{
            "missing_keywords": ["keyword1", "keyword2"],
            "present_keywords": ["keyword1", "keyword2"],
            "keyword_density_score": <0-100 integer>
        }},
        "section_recommendations": {{
            "skills": "recommendation for skills section",
            "experience": "recommendation for experience section",
            "education": "recommendation for education section"
        }}
    }}
    
    Be specific and actionable in your recommendations.
    """
    enhancement_prompt = f"""
    Based on this resume and job description, generate enhanced content:
    
    RESUME:
    {resume_text}
    
    JOB DESCRIPTION:
    {job_description}
    
    Generate enhanced versions in JSON format:
    {{
        "enhanced_summary": "An improved professional summary tailored to the job",
        "enhanced_skills": ["skill1", "skill2", "skill3"],
        "enhanced_experience_bullets": [
            "Enhanced bullet point 1 with metrics and keywords",
            "Enhanced bullet point 2 with impact and results",
            "Enhanced bullet point 3 with relevant achievements"
        ],
        "cover_letter_outline": {{
            "opening": "Compelling opening paragraph",
            "body": "Main body highlighting relevant experience",
            "closing": "Strong closing paragraph"
        }}
    }}
    
    Focus on incorporating job-relevant keywords and quantifiable achievements.
    """
    if model_type == "OpenAI":
        client = OpenAI(api_key=api_key)
        try:
            analysis_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert career coach and resume analyst. Provide detailed, actionable feedback in valid JSON format only."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            analysis_text = analysis_response.choices[0].message.content.strip()
            analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            analysis_data = json.loads(analysis_text)
            enhancement_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Generate enhanced, job-tailored content in valid JSON format only."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.4
            )
            enhancement_text = enhancement_response.choices[0].message.content.strip()
            enhancement_text = enhancement_text.replace('```json', '').replace('```', '').strip()
            enhancement_data = json.loads(enhancement_text)
            result = {
                "success": True,
                "analysis": analysis_data,
                "enhancements": enhancement_data,
                "metadata": {
                    "model_used": model,
                    "model_type": model_type,
                    "timestamp": json.dumps({"timestamp": "2024-01-01T00:00:00Z"}),
                    "resume_sections_analyzed": list(resume_json.keys())
                }
            }
            return result
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "Failed to parse AI response as JSON",
                "raw_analysis": analysis_text if 'analysis_text' in locals() else "",
                "raw_enhancement": enhancement_text if 'enhancement_text' in locals() else ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}"
            }
    else:
        return {
            "success": False,
            "error": f"Model type '{model_type}' not supported for AI enhancement"
        }

if __name__ == '__main__':
    # Minimal debug
    print("Starting Flask application")
    app.run(debug=True, host='0.0.0.0', port=5000)
def health_check():
    """Health check endpoint"""
    print("=== DEBUG: Health check requested ===")
    response_data = {
        "status": "healthy",
        "message": "GenApply API is running",
        "endpoints": [
            "/api/extract-resume-json",
            "/api/generate-cover-letter", 
            "/api/optimize-resume",
            "/api/ai-enhance",
            "/api/templates"
        ]
    }
    print(f"DEBUG: Health check response: {response_data}")
    return jsonify(response_data)

@app.errorhandler(404)
def not_found(error):
    print(f"DEBUG: 404 error - endpoint not found: {request.url}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"DEBUG: 500 error - internal server error: {str(error)}")
    print(f"DEBUG: 500 error traceback: {traceback.format_exc()}")
    return jsonify({"error": "Internal server error"}), 500

@app.route('/api/ai-enhance', methods=['POST'])
def ai_enhance():
    """AI Enhancement API - analyze resume against job description and provide optimized content"""
    try:
        print("=== DEBUG: Starting ai_enhance ===")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request content type: {request.content_type}")
        
        # Handle both file upload and JSON input
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Get file_id for request tracking
            file_id = request.form.get('file_id', 'unknown')
            print(f"DEBUG: File ID: {file_id}")
            
            # File upload mode
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded", "file_id": file_id}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected", "file_id": file_id}), 400
            
            # Extract form data
            job_description = request.form.get('job_description', '')
            api_key = request.form.get('api_key')
            model_type = request.form.get('model_type', 'OpenAI')
            model = request.form.get('model', 'gpt-4o')
            
            print(f"DEBUG: [File ID: {file_id}] File upload mode - filename: {file.filename}")
            
            # Extract text from file
            text = extract_text_from_upload(file)
            print(f"DEBUG: [File ID: {file_id}] Text extracted, length: {len(text)}")
            
            # Generate JSON resume
            resume_json = generate_json_resume(text, api_key, model, model_type)
            
        else:
            # JSON input mode - support both file_id and resume_json
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided", "file_id": "unknown"}), 400
            
            # Get file_id for request tracking
            file_id = data.get('file_id', 'unknown')
            print(f"DEBUG: File ID: {file_id}")
            
            # Try to get resume from file_id first, fallback to direct resume_json
            resume_json = data.get('resume_json')
            if not resume_json and file_id != 'unknown':
                resume_json = get_resume_data(file_id)
                if resume_json is None:
                    return jsonify({"error": "Resume data not found. Please provide resume_json or re-upload your resume.", "file_id": file_id}), 404
            
            job_description = data.get('job_description', '')
            api_key = data.get('api_key')
            model_type = data.get('model_type', 'OpenAI')
            model = data.get('model', 'gpt-4o')
            
            print(f"DEBUG: [File ID: {file_id}] JSON input mode")
        
        # Validate required fields
        if not all([resume_json, job_description, api_key]):
            missing = []
            if not resume_json: missing.append('resume_json')
            if not job_description: missing.append('job_description')
            if not api_key: missing.append('api_key')
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}", "file_id": file_id}), 400
        
        print(f"DEBUG: [File ID: {file_id}] Job description length: {len(job_description)}")
        print(f"DEBUG: [File ID: {file_id}] Resume JSON keys: {list(resume_json.keys()) if isinstance(resume_json, dict) else 'Not a dict'}")
        
        # Generate AI analysis and enhancement
        enhancement_result = generate_ai_enhancement(resume_json, job_description, api_key, model, model_type)
        
        # Add file_id to response
        enhancement_result['file_id'] = file_id
        
        print(f"DEBUG: [File ID: {file_id}] Enhancement result keys: {list(enhancement_result.keys())}")
        return jsonify(enhancement_result)
        
    except Exception as e:
        file_id = 'unknown'
        if request.content_type and 'multipart/form-data' in request.content_type:
            file_id = request.form.get('file_id', 'unknown')
        elif request.get_json():
            file_id = request.get_json().get('file_id', 'unknown')
        
        print(f"DEBUG: [File ID: {file_id}] Error in ai_enhance: {str(e)}")
        print(f"DEBUG: [File ID: {file_id}] Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Failed to enhance resume: {str(e)}",
            "traceback": traceback.format_exc(),
            "file_id": file_id
        }), 500

def generate_ai_enhancement(resume_json, job_description, api_key, model="gpt-4o", model_type="OpenAI"):
    """Generate AI-powered enhancement analysis and content"""
    from openai import OpenAI
    
    # Convert resume to text for analysis
    resume_text = json.dumps(resume_json, indent=2)
    
    # Analysis prompt
    analysis_prompt = f"""
    Analyze the following resume against the job description and provide a comprehensive assessment.
    
    RESUME:
    {resume_text}
    
    JOB DESCRIPTION:
    {job_description}
    
    Provide your analysis in the following JSON format:
    {{
        "match_score": <0-100 integer>,
        "strengths": ["strength1", "strength2", "strength3"],
        "gaps": ["gap1", "gap2", "gap3"],
        "suggestions": ["suggestion1", "suggestion2", "suggestion3"],
        "keyword_analysis": {{
            "missing_keywords": ["keyword1", "keyword2"],
            "present_keywords": ["keyword1", "keyword2"],
            "keyword_density_score": <0-100 integer>
        }},
        "section_recommendations": {{
            "skills": "recommendation for skills section",
            "experience": "recommendation for experience section",
            "education": "recommendation for education section"
        }}
    }}
    
    Be specific and actionable in your recommendations.
    """
    
    # Enhancement prompt
    enhancement_prompt = f"""
    Based on this resume and job description, generate enhanced content:
    
    RESUME:
    {resume_text}
    
    JOB DESCRIPTION:
    {job_description}
    
    Generate enhanced versions in JSON format:
    {{
        "enhanced_summary": "An improved professional summary tailored to the job",
        "enhanced_skills": ["skill1", "skill2", "skill3"],
        "enhanced_experience_bullets": [
            "Enhanced bullet point 1 with metrics and keywords",
            "Enhanced bullet point 2 with impact and results",
            "Enhanced bullet point 3 with relevant achievements"
        ],
        "cover_letter_outline": {{
            "opening": "Compelling opening paragraph",
            "body": "Main body highlighting relevant experience",
            "closing": "Strong closing paragraph"
        }}
    }}
    
    Focus on incorporating job-relevant keywords and quantifiable achievements.
    """
    
    print("DEBUG: Generating AI analysis...")
    
    if model_type == "OpenAI":
        client = OpenAI(api_key=api_key)
        
        try:
            # Get analysis
            analysis_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert career coach and resume analyst. Provide detailed, actionable feedback in valid JSON format only."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            analysis_text = analysis_response.choices[0].message.content.strip()
            print(f"DEBUG: Analysis response length: {len(analysis_text)}")
            
            # Clean and parse JSON
            analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            analysis_data = json.loads(analysis_text)
            
            # Get enhancement
            enhancement_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Generate enhanced, job-tailored content in valid JSON format only."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.4
            )
            
            enhancement_text = enhancement_response.choices[0].message.content.strip()
            print(f"DEBUG: Enhancement response length: {len(enhancement_text)}")
            
            # Clean and parse JSON
            enhancement_text = enhancement_text.replace('```json', '').replace('```', '').strip()
            enhancement_data = json.loads(enhancement_text)
            
            # Combine results
            result = {
                "success": True,
                "analysis": analysis_data,
                "enhancements": enhancement_data,
                "metadata": {
                    "model_used": model,
                    "model_type": model_type,
                    "timestamp": json.dumps({"timestamp": "2024-01-01T00:00:00Z"}),
                    "resume_sections_analyzed": list(resume_json.keys())
                }
            }
            
            print(f"DEBUG: Combined result keys: {list(result.keys())}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {str(e)}")
            return {
                "success": False,
                "error": "Failed to parse AI response as JSON",
                "raw_analysis": analysis_text if 'analysis_text' in locals() else "",
                "raw_enhancement": enhancement_text if 'enhancement_text' in locals() else ""
            }
        except Exception as e:
            print(f"DEBUG: OpenAI API error: {str(e)}")
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}"
            }
    
    else:
        return {
            "success": False,
            "error": f"Model type '{model_type}' not supported for AI enhancement"
        }

if __name__ == '__main__':
    print("=== DEBUG: Starting Flask application ===")
    print("DEBUG: Flask app configuration:")
    print(f"  - Debug mode: True")
    print(f"  - Host: 0.0.0.0")
    print(f"  - Port: 5000")
    print("DEBUG: CORS enabled for all routes")
    print("DEBUG: Resume storage configured:")
    print(f"  - Storage directory: {RESUME_STORAGE_DIR}")
    print("DEBUG: Available endpoints:")
    print("  - GET  /api/health")
    print("  - GET  /api/templates")
    print("  - POST /api/extract-resume-json")
    print("  - POST /api/generate-cover-letter")
    print("  - POST /api/optimize-resume")
    print("  - POST /api/ai-enhance")
    app.run(debug=True, host='0.0.0.0', port=5000)
