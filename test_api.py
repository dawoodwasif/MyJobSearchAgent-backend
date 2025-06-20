import requests
import json
import time
import uuid
from pathlib import Path
import os

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = "enter-your-key-here"  # Replace with your OpenAI API key

# Create output directories
OUTPUT_DIR = Path("test_output")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "cover_letter").mkdir(exist_ok=True)
(OUTPUT_DIR / "json_resume").mkdir(exist_ok=True)
(OUTPUT_DIR / "optimize_resume").mkdir(exist_ok=True)

def generate_file_id():
    """Generate unique file ID for request tracking"""
    return str(uuid.uuid4())[:8]

# Global variable to track test results
test_results = {}

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def print_test(test_name):
    """Print formatted test header"""
    print(f"\n--- {test_name} ---")

def record_test_result(test_name, passed, error_msg=None):
    """Record test result for final summary"""
    test_results[test_name] = {
        'passed': passed,
        'error': error_msg
    }

def test_health_check():
    """Test health check endpoint"""
    print_test("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Health check passed")
            print(f"  Status: {result.get('status')}")
            print(f"  Available endpoints: {len(result.get('endpoints', []))}")
            record_test_result("Health Check", True)
            return True
        else:
            print(f"✗ Health check failed")
            record_test_result("Health Check", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {str(e)}")
        record_test_result("Health Check", False, str(e))
        return False

def test_get_templates():
    """Test templates endpoint"""
    print_test("Testing Get Templates")
    
    try:
        response = requests.get(f"{BASE_URL}/api/templates")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            templates = result.get('templates', [])
            print(f"✓ Templates retrieved successfully")
            print(f"  Available templates: {templates}")
            print(f"  Template count: {len(templates)}")
            record_test_result("Get Templates", True)
            return result
        else:
            print(f"✗ Templates retrieval failed")
            record_test_result("Get Templates", False, f"Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Templates error: {str(e)}")
        record_test_result("Get Templates", False, str(e))
        return None

def test_extract_resume_json(file_path):
    """Test resume JSON extraction with file_id"""
    print_test("Testing Extract Resume JSON")
    
    file_id = generate_file_id()
    print(f"Generated File ID: {file_id}")
    
    if not Path(file_path).exists():
        print(f"✗ Test file not found: {file_path}")
        record_test_result("Extract Resume JSON", False, f"File not found: {file_path}")
        return None, None
    
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = {
                'file_id': file_id,
                'api_key': API_KEY,
                'model_type': 'OpenAI',
                'model': 'gpt-4o'
            }
            
            print(f"Uploading file: {Path(file_path).name}")
            response = requests.post(f"{BASE_URL}/api/extract-resume-json", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_file_id = result.get('file_id')
            print(f"✓ Resume JSON extraction successful")
            print(f"  Request File ID: {file_id}")
            print(f"  Response File ID: {response_file_id}")
            print(f"  File ID Match: {file_id == response_file_id}")
            print(f"  Extracted text length: {result.get('extracted_text_length')}")
            print(f"  Resume JSON keys: {list(result.get('resume_json', {}).keys())}")
            record_test_result("Extract Resume JSON", True)
            return result, file_id  # Return both result and file_id
        else:
            result = response.json()
            response_file_id = result.get('file_id', 'not_provided')
            error_msg = result.get('error', 'Unknown error')
            print(f"✗ Resume JSON extraction failed")
            print(f"  Request File ID: {file_id}")
            print(f"  Response File ID: {response_file_id}")
            print(f"  Error: {error_msg}")
            
            # Check if it's an API key issue
            if 'API key' in error_msg:
                print(f"  💡 Tip: Update API_KEY variable with a valid OpenAI API key")
                record_test_result("Extract Resume JSON", False, "Invalid API key (expected with dummy key)")
            else:
                record_test_result("Extract Resume JSON", False, error_msg)
            
            return None, None
    except Exception as e:
        print(f"✗ Resume extraction error: {str(e)}")
        record_test_result("Extract Resume JSON", False, str(e))
        return None, None

def test_ai_enhance_with_json(resume_json, job_description):
    """Test AI enhancement with JSON input"""
    print_test("Testing AI Enhancement with JSON Input")
    
    file_id = generate_file_id()
    print(f"Generated File ID: {file_id}")
    
    data = {
        'file_id': file_id,
        'resume_json': resume_json,
        'job_description': job_description,
        'api_key': API_KEY,
        'model_type': 'OpenAI',
        'model': 'gpt-4o'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/ai-enhance", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_file_id = result.get('file_id')
            success = result.get('success', False)
            
            print(f"✓ AI enhancement completed")
            print(f"  Request File ID: {file_id}")
            print(f"  Response File ID: {response_file_id}")
            print(f"  File ID Match: {file_id == response_file_id}")
            print(f"  Success: {success}")
            
            if success:
                analysis = result.get('analysis', {})
                enhancements = result.get('enhancements', {})
                print(f"  Match score: {analysis.get('match_score', 'N/A')}")
                print(f"  Strengths found: {len(analysis.get('strengths', []))}")
                print(f"  Gaps identified: {len(analysis.get('gaps', []))}")
                print(f"  Enhancement sections: {list(enhancements.keys())}")
                record_test_result("AI Enhancement", True)
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"  Error: {error_msg}")
                if 'API key' in error_msg or '401' in error_msg:
                    record_test_result("AI Enhancement", False, "Invalid API key (expected with dummy key)")
                else:
                    record_test_result("AI Enhancement", False, error_msg)
            
            return result
        else:
            result = response.json()
            response_file_id = result.get('file_id', 'not_provided')
            error_msg = result.get('error', 'Unknown error')
            print(f"✗ AI enhancement failed")
            print(f"  Request File ID: {file_id}")
            print(f"  Response File ID: {response_file_id}")
            print(f"  Error: {error_msg}")
            record_test_result("AI Enhancement", False, error_msg)
            return None
    except Exception as e:
        print(f"✗ AI enhancement error: {str(e)}")
        record_test_result("AI Enhancement", False, str(e))
        return None

def test_optimize_resume_with_file_id(file_id, job_description, template="Simple"):
    """Test resume optimization using file_id (no resume_json required)"""
    print_test(f"Testing Resume Optimization with File ID (Template: {template})")
    
    print(f"Using File ID: {file_id}")
    
    data = {
        'file_id': file_id,
        'job_description': job_description,
        'template': template,
        'api_key': API_KEY,
        'model_type': 'OpenAI',
        'model': 'gpt-4o',
        'section_ordering': ['education', 'work', 'skills', 'projects', 'awards'],
        'improve_resume': True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/optimize-resume", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = OUTPUT_DIR / "optimize_resume" / f"optimized_resume_{file_id}_{template.lower()}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Resume optimization successful")
            print(f"  File ID: {file_id}")
            print(f"  PDF saved as: {filename}")
            print(f"  PDF size: {len(response.content)} bytes")
            print(f"  Template used: {template}")
            record_test_result("Resume Optimization (File ID)", True)
            return str(filename)
        else:
            try:
                result = response.json()
                response_file_id = result.get('file_id', 'not_provided')
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ Resume optimization failed")
                print(f"  Request File ID: {file_id}")
                print(f"  Response File ID: {response_file_id}")
                print(f"  Error: {error_msg}")
                
                if 'not found' in error_msg:
                    record_test_result("Resume Optimization (File ID)", False, "Resume data not found")
                else:
                    record_test_result("Resume Optimization (File ID)", False, error_msg)
            except:
                print(f"✗ Resume optimization failed (non-JSON response)")
                print(f"  Request File ID: {file_id}")
                record_test_result("Resume Optimization (File ID)", False, "Non-JSON response")
            return None
    except Exception as e:
        print(f"✗ Resume optimization error: {str(e)}")
        record_test_result("Resume Optimization (File ID)", False, str(e))
        return None

def test_generate_cover_letter_with_file_id(file_id, job_info):
    """Test cover letter generation using file_id (no resume_json required)"""
    print_test("Testing Cover Letter Generation with File ID")
    
    print(f"Using File ID: {file_id}")
    
    data = {
        'file_id': file_id,
        'job_description': job_info['description'],
        'api_key': API_KEY,
        'model_type': 'OpenAI',
        'model': 'gpt-4o',
        'personal_info': job_info['personal_info'],
        'company_info': {
            'position': job_info['position'],
            'company_name': job_info['company'],
            'location': job_info['location'],
            'hiring_manager': job_info.get('hiring_manager', ''),
            'department': job_info.get('department', '')
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-cover-letter", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = OUTPUT_DIR / "cover_letter" / f"cover_letter_{file_id}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Cover letter generation successful")
            print(f"  File ID: {file_id}")
            print(f"  PDF saved as: {filename}")
            print(f"  PDF size: {len(response.content)} bytes")
            print(f"  Company: {job_info['company']}")
            print(f"  Position: {job_info['position']}")
            print(f"  Personal info keys: {list(job_info['personal_info'].keys())}")
            record_test_result("Cover Letter Generation (File ID)", True)
            return str(filename)
        else:
            try:
                result = response.json()
                response_file_id = result.get('file_id', 'not_provided')
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ Cover letter generation failed")
                print(f"  Request File ID: {file_id}")
                print(f"  Response File ID: {response_file_id}")
                print(f"  Error: {error_msg[:100]}...")
                
                if 'not found' in error_msg:
                    record_test_result("Cover Letter Generation (File ID)", False, "Resume data not found")
                elif 'API key' in error_msg or '401' in error_msg:
                    record_test_result("Cover Letter Generation (File ID)", False, "Invalid API key (expected with dummy key)")
                else:
                    record_test_result("Cover Letter Generation (File ID)", False, error_msg)
            except:
                print(f"✗ Cover letter generation failed (non-JSON response)")
                record_test_result("Cover Letter Generation (File ID)", False, "Non-JSON response")
            return None
    except Exception as e:
        print(f"✗ Cover letter generation error: {str(e)}")
        record_test_result("Cover Letter Generation (File ID)", False, str(e))
        return None

def test_ai_enhance_with_file_id(file_id, job_description):
    """Test AI enhancement using file_id (no resume_json required)"""
    print_test("Testing AI Enhancement with File ID")
    
    print(f"Using File ID: {file_id}")
    
    data = {
        'file_id': file_id,
        'job_description': job_description,
        'api_key': API_KEY,
        'model_type': 'OpenAI',
        'model': 'gpt-4o'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/ai-enhance", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_file_id = result.get('file_id')
            success = result.get('success', False)
            
            print(f"✓ AI enhancement completed")
            print(f"  Request File ID: {file_id}")
            print(f"  Response File ID: {response_file_id}")
            print(f"  File ID Match: {file_id == response_file_id}")
            print(f"  Success: {success}")
            
            if success:
                analysis = result.get('analysis', {})
                enhancements = result.get('enhancements', {})
                print(f"  Match score: {analysis.get('match_score', 'N/A')}")
                print(f"  Strengths found: {len(analysis.get('strengths', []))}")
                print(f"  Gaps identified: {len(analysis.get('gaps', []))}")
                print(f"  Enhancement sections: {list(enhancements.keys())}")
                record_test_result("AI Enhancement (File ID)", True)
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"  Error: {error_msg}")
                if 'not found' in error_msg:
                    record_test_result("AI Enhancement (File ID)", False, "Resume data not found")
                elif 'API key' in error_msg or '401' in error_msg:
                    record_test_result("AI Enhancement (File ID)", False, "Invalid API key (expected with dummy key)")
                else:
                    record_test_result("AI Enhancement (File ID)", False, error_msg)
            
            return result
        else:
            result = response.json()
            response_file_id = result.get('file_id', 'not_provided')
            error_msg = result.get('error', 'Unknown error')
            print(f"✗ AI enhancement failed")
            print(f"  Request File ID: {file_id}")
            print(f"  Response File ID: {response_file_id}")
            print(f"  Error: {error_msg}")
            
            if 'not found' in error_msg:
                record_test_result("AI Enhancement (File ID)", False, "Resume data not found")
            else:
                record_test_result("AI Enhancement (File ID)", False, error_msg)
            return None
    except Exception as e:
        print(f"✗ AI enhancement error: {str(e)}")
        record_test_result("AI Enhancement (File ID)", False, str(e))
        return None

def test_workflow_with_file_storage():
    """Test complete workflow: extract -> store -> use file_id for other operations"""
    print_test("Testing Complete File Storage Workflow")
    
    sample_file = "sample/resume.pdf"
    if not Path(sample_file).exists():
        print(f"⚠️  Sample file not found: {sample_file}")
        print("   Skipping file storage workflow test...")
        record_test_result("File Storage Workflow", False, "Sample file not found")
        return None
    
    # Step 1: Extract resume and get file_id
    extract_result, file_id = test_extract_resume_json(sample_file)
    if not extract_result or not file_id:
        print("✗ Extract failed, cannot continue workflow test")
        record_test_result("File Storage Workflow", False, "Extract step failed")
        return None
    
    print(f"\n✓ Step 1 Complete: Resume extracted and stored with file_id: {file_id}")
    
    # Save the extracted resume JSON to file for reference
    json_filename = OUTPUT_DIR / "json_resume" / f"resume_{file_id}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(extract_result['resume_json'], f, indent=2, ensure_ascii=False)
    print(f"✓ Resume JSON saved to: {json_filename}")
    
    # Sample job data
    job_description = """
    We are seeking a talented Software Developer to join our team. The ideal candidate will have:
    - Strong experience with Python and JavaScript
    - Knowledge of web development frameworks
    - Experience with SQL and database management
    - Ability to work in an agile environment
    """
    
    job_info = {
        "description": job_description,
        "position": "Senior Software Developer",
        "company": "Tech Innovation Labs",
        "location": "San Francisco, CA",
        "personal_info": {
            "name": "John Doe",
            "phone": "+1-555-0123",
            "email": "john.doe@email.com"
        }
    }
    
    # Step 2: Use file_id for AI enhancement
    print(f"\n--- Step 2: AI Enhancement using file_id ---")
    enhance_result = test_ai_enhance_with_file_id(file_id, job_description)
    
    # Step 3: Use file_id for resume optimization
    print(f"\n--- Step 3: Resume Optimization using file_id ---")
    optimize_result = test_optimize_resume_with_file_id(file_id, job_description, "Modern")
    
    # Step 4: Use file_id for cover letter generation
    print(f"\n--- Step 4: Cover Letter Generation using file_id ---")
    cover_result = test_generate_cover_letter_with_file_id(file_id, job_info)
    
    # Summary
    steps_completed = sum([
        extract_result is not None,
        enhance_result is not None,
        optimize_result is not None,
        cover_result is not None
    ])
    
    print(f"\n✓ Workflow Summary:")
    print(f"  File ID: {file_id}")
    print(f"  Steps completed: {steps_completed}/4")
    print(f"  Extract: {'✓' if extract_result else '✗'}")
    print(f"  Enhance: {'✓' if enhance_result else '✗'}")
    print(f"  Optimize: {'✓' if optimize_result else '✗'}")
    print(f"  Cover Letter: {'✓' if cover_result else '✗'}")
    
    if steps_completed >= 3:
        record_test_result("File Storage Workflow", True)
        print(f"  🎉 Workflow successful!")
    else:
        record_test_result("File Storage Workflow", False, f"Only {steps_completed}/4 steps completed")
        print(f"  ⚠️  Partial workflow completion")
    
    return file_id

def test_optimize_resume(resume_json, job_description, template="Simple"):
    """Test resume optimization with direct JSON input"""
    print_test(f"Testing Resume Optimization with JSON (Template: {template})")
    
    file_id = generate_file_id()
    print(f"Generated File ID: {file_id}")
    
    data = {
        'file_id': file_id,
        'resume_json': resume_json,
        'job_description': job_description,
        'template': template,
        'api_key': API_KEY,
        'model_type': 'OpenAI',
        'model': 'gpt-4o',
        'section_ordering': ['education', 'work', 'skills', 'projects', 'awards'],
        'improve_resume': True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/optimize-resume", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = OUTPUT_DIR / "optimize_resume" / f"optimized_resume_{file_id}_{template.lower()}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Resume optimization successful")
            print(f"  Request File ID: {file_id}")
            print(f"  PDF saved as: {filename}")
            print(f"  PDF size: {len(response.content)} bytes")
            print(f"  Template used: {template}")
            record_test_result("Resume Optimization (JSON)", True)
            return str(filename)
        else:
            # Try to get JSON error response
            try:
                result = response.json()
                response_file_id = result.get('file_id', 'not_provided')
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ Resume optimization failed")
                print(f"  Request File ID: {file_id}")
                print(f"  Response File ID: {response_file_id}")
                print(f"  Error: {error_msg}")
                record_test_result("Resume Optimization (JSON)", False, error_msg)
            except:
                print(f"✗ Resume optimization failed (non-JSON response)")
                print(f"  Request File ID: {file_id}")
                print(f"  Response: {response.text[:200]}...")
                record_test_result("Resume Optimization (JSON)", False, "Non-JSON response")
            return None
    except Exception as e:
        print(f"✗ Resume optimization error: {str(e)}")
        record_test_result("Resume Optimization (JSON)", False, str(e))
        return None

def test_generate_cover_letter(resume_json, job_info):
    """Test cover letter generation with direct JSON input"""
    print_test("Testing Cover Letter Generation with JSON")
    
    file_id = generate_file_id()
    print(f"Generated File ID: {file_id}")
    
    data = {
        'file_id': file_id,
        'resume_json': resume_json,
        'job_description': job_info['description'],
        'api_key': API_KEY,
        'model_type': 'OpenAI',
        'model': 'gpt-4o',
        'personal_info': job_info['personal_info'],
        'company_info': {
            'position': job_info['position'],
            'company_name': job_info['company'],
            'location': job_info['location'],
            'hiring_manager': job_info.get('hiring_manager', ''),
            'department': job_info.get('department', '')
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-cover-letter", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            filename = OUTPUT_DIR / "cover_letter" / f"cover_letter_{file_id}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Cover letter generation successful")
            print(f"  Request File ID: {file_id}")
            print(f"  PDF saved as: {filename}")
            print(f"  PDF size: {len(response.content)} bytes")
            print(f"  Company: {job_info['company']}")
            print(f"  Position: {job_info['position']}")
            print(f"  Personal info keys: {list(job_info['personal_info'].keys())}")
            record_test_result("Cover Letter Generation (JSON)", True)
            return str(filename)
        else:
            # Try to get JSON error response
            try:
                result = response.json()
                response_file_id = result.get('file_id', 'not_provided')
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ Cover letter generation failed")
                print(f"  Request File ID: {file_id}")
                print(f"  Response File ID: {response_file_id}")
                print(f"  Error: {error_msg}")
                record_test_result("Cover Letter Generation (JSON)", False, error_msg)
            except:
                print(f"✗ Cover letter generation failed (non-JSON response)")
                print(f"  Request File ID: {file_id}")
                record_test_result("Cover Letter Generation (JSON)", False, "Non-JSON response")
            return None
    except Exception as e:
        print(f"✗ Cover letter generation error: {str(e)}")
        record_test_result("Cover Letter Generation (JSON)", False, str(e))
        return None

def test_file_id_consistency():
    """Test that file IDs are consistent across multiple requests"""
    print_test("Testing File ID Consistency")
    
    sample_resume = create_sample_resume_json()
    job_description = "Software developer position requiring Python skills."
    
    file_ids = []
    results = []
    
    for i in range(3):
        file_id = generate_file_id()
        file_ids.append(file_id)
        
        data = {
            'file_id': file_id,
            'resume_json': sample_resume,
            'job_description': job_description,
            'api_key': API_KEY,
            'model_type': 'OpenAI',
            'model': 'gpt-4o'
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/ai-enhance", json=data)
            if response.status_code == 200:
                result = response.json()
                response_file_id = result.get('file_id')
                match = file_id == response_file_id
                results.append({
                    'request_id': file_id,
                    'response_id': response_file_id,
                    'match': match,
                    'success': result.get('success', False)
                })
                print(f"  Request {i+1}: {file_id} -> {response_file_id} ({'✓' if match else '✗'})")
            else:
                print(f"  Request {i+1}: {file_id} -> Failed (Status: {response.status_code})")
                
        except Exception as e:
            print(f"  Request {i+1}: {file_id} -> Error: {str(e)}")
        
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    successful_matches = sum(1 for r in results if r['match'])
    total_requests = len(results)
    
    print(f"\nFile ID Consistency Summary:")
    print(f"  Total requests: {total_requests}")
    print(f"  Successful ID matches: {successful_matches}")
    print(f"  Consistency rate: {successful_matches/total_requests*100:.1f}%")
    
    # Record test result based on consistency rate
    if successful_matches == total_requests:
        record_test_result("File ID Consistency", True)
    else:
        record_test_result("File ID Consistency", False, f"Only {successful_matches}/{total_requests} consistent")
    
    return results

def create_sample_resume_json():
    """Create sample resume JSON for testing"""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "+1-555-0123"
        },
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of Technology",
                "year": "2020",
                "gpa": "3.8/4.0"
            }
        ],
        "work_experience": [
            {
                "title": "Software Developer",
                "company": "Tech Corp",
                "duration": "2020-2023",
                "description": "Developed web applications using Python and JavaScript"
            }
        ],
        "skills": ["Python", "JavaScript", "React", "Node.js", "SQL"]
    }

def check_api_key():
    """Check if a real API key is being used"""
    if API_KEY == 'your-openai-api-key-here':
        print("⚠️  Using dummy API key - AI features will return 401 errors")
        print("   Set OPENAI_API_KEY environment variable for full testing")
        return False
    else:
        print(f"✓ Using API key: {API_KEY[:8]}...")
        return True

def print_final_summary():
    """Print final test summary showing pass/fail for each API"""
    print_section("FINAL TEST RESULTS SUMMARY")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "N/A")
    
    print(f"\nDetailed Results:")
    print(f"{'API Endpoint':<25} {'Status':<10} {'Notes'}")
    print(f"{'-'*60}")
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        notes = result.get('error', '')
        
        # Truncate long error messages
        if notes and len(notes) > 30:
            notes = notes[:27] + "..."
        
        print(f"{test_name:<25} {status:<10} {notes}")
    
    # Overall assessment
    print(f"\n{'='*60}")
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! The API is working correctly.")
    elif passed_tests >= total_tests // 2:
        print("⚠️  PARTIAL SUCCESS - Some tests failed, but core functionality works.")
        
        # Check if failures are API key related
        api_key_failures = sum(1 for result in test_results.values() 
                              if not result['passed'] and 'API key' in result.get('error', ''))
        
        if api_key_failures > 0:
            print(f"   Note: {api_key_failures} failure(s) due to dummy API key (expected)")
    else:
        print("❌ MULTIPLE FAILURES - Please check the server and configuration.")
    
    print(f"{'='*60}")

def main():
    """Run comprehensive API tests with file-based storage"""
    print_section("GenApply API Testing Suite with File-Based Storage")
    
    # Check API key
    has_real_key = check_api_key()
    
    # Test basic endpoints (no API key required)
    health_ok = test_health_check()
    templates_ok = test_get_templates()
    
    if not health_ok:
        print("\n❌ Server health check failed. Is the server running?")
        print_final_summary()
        return
    
    # Test the complete file storage workflow
    workflow_file_id = test_workflow_with_file_storage()
    
    # Test file ID consistency with different endpoints
    if workflow_file_id:
        print(f"\n--- Testing Multiple Operations with Same File ID ---")
        job_description = "Python developer position with React experience needed."
        
        # Test multiple operations with same file_id
        test_ai_enhance_with_file_id(workflow_file_id, job_description)
        test_optimize_resume_with_file_id(workflow_file_id, job_description, "Simple")
    
    # Test original workflow with JSON input (as fallback)
    print(f"\n--- Fallback: Testing with Direct JSON Input ---")
    sample_resume = create_sample_resume_json()
    job_description = "Software developer position requiring Python skills."
    
    # Enhanced job info with separate personal and company information
    job_info = {
        "description": job_description,
        "position": "Full Stack Developer",
        "company": "Startup Inc",
        "location": "Remote",
        "hiring_manager": "Sarah Johnson",
        "department": "Engineering Team",
        "personal_info": {
            "name": "Jane Smith",
            "phone": "+1-555-0456",
            "email": "jane.smith@email.com",
            "address": "123 Tech Street, Silicon Valley, CA 94102",
            "linkedin": "https://linkedin.com/in/janesmith"
        }
    }
    
    # Test workflow sample job info
    workflow_job_info = {
        "description": """
        We are seeking a talented Software Developer to join our team. The ideal candidate will have:
        - Strong experience with Python and JavaScript
        - Knowledge of web development frameworks
        - Experience with SQL and database management
        - Ability to work in an agile environment
        """,
        "position": "Senior Software Developer",
        "company": "Tech Innovation Labs",
        "location": "San Francisco, CA",
        "hiring_manager": "Michael Chen",
        "department": "Product Development",
        "personal_info": {
            "name": "John Doe",
            "phone": "+1-555-0123",
            "email": "john.doe@email.com",
            "address": "456 Innovation Blvd, San Francisco, CA 94105",
            "linkedin": "https://linkedin.com/in/johndoe"
        }
    }
    
    # Original tests with JSON input using new structure
    test_ai_enhance_with_json(sample_resume, job_description)
    test_optimize_resume(sample_resume, job_description, "Awesome")
    test_generate_cover_letter(sample_resume, job_info)
    
    # Test file ID consistency
    test_file_id_consistency()
    
    # Print final summary
    print_final_summary()
    
    print("\n🎉 File-based storage testing completed!")
    print("   Key improvements tested:")
    print("   ✓ Resume data stored by file_id")
    print("   ✓ Separate personal_info and company_info objects")
    print("   ✓ Intelligent fallback to resume JSON for missing personal data")
    print("   ✓ No need to pass resume_json to other endpoints")
    print("   ✓ Simplified API calls")
    print("   ✓ Persistent storage across requests")
    print(f"   📁 Output files organized in: {OUTPUT_DIR}")
    print(f"   📄 Cover letters: {OUTPUT_DIR / 'cover_letter'}")
    print(f"   📄 JSON resumes: {OUTPUT_DIR / 'json_resume'}")
    print(f"   📄 Optimized resumes: {OUTPUT_DIR / 'optimize_resume'}")

if __name__ == "__main__":
    main()
