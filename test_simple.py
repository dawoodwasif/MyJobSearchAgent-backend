import requests
from pathlib import Path
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"
SAMPLE_FOLDER = Path("sample")

# DeepSeek API key
API_KEY = "api-key"  # DeepSeek API key

# Default model configuration
DEFAULT_MODEL_TYPE = "DeepSeek"
DEFAULT_MODEL = "deepseek-chat"

def test_health_first():
    """Test if the API is responding at all"""
    print("Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✓ API is healthy")
            return True
        else:
            print(f"✗ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot reach API: {str(e)}")
        return False

def test_with_smaller_file():
    """Test with a simple text file first"""
    print("\nTesting with a simple text file...")
    
    # Create a small test file
    test_content = "John Doe\nSoftware Engineer\nPython, JavaScript, React\nExperience: 5 years"
    
    try:
        # Send as text file
        files = {'file': ('test_resume.txt', test_content.encode(), 'text/plain')}
        data = {
            'api_key': API_KEY,
            'model_type': DEFAULT_MODEL_TYPE,
            'model': DEFAULT_MODEL
        }
        
        response = requests.post(f"{API_BASE_URL}/extract-resume-json", 
                               files=files, data=data, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Text file processing successful!")
            print(f"Text length: {result.get('extracted_text_length', 0)}")
            return True
        else:
            print("✗ Text file processing failed:")
            try:
                print(response.json())
            except:
                print(response.text)
            return False
            
    except Exception as e:
        print(f"✗ Error testing text file: {str(e)}")
        return False

def test_file_upload_debug():
    """Debug file upload issue"""
    print("\nTesting PDF file upload...")
    
    # Find resume file
    resume_files = list(SAMPLE_FOLDER.glob("*.pdf")) + list(SAMPLE_FOLDER.glob("*.docx"))
    if not resume_files:
        print("No resume files found in sample folder")
        return
    
    resume_file = resume_files[0]
    print(f"Using file: {resume_file}")
    print(f"File size: {resume_file.stat().st_size} bytes")
    
    # Check if file is too large (Flask has default limits)
    file_size_mb = resume_file.stat().st_size / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 16:
        print("⚠️  File is quite large. Flask default limit is 16MB.")
    
    # Determine correct MIME type based on file extension
    mime_type = 'application/pdf' if resume_file.suffix.lower() == '.pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    print(f"MIME type: {mime_type}")
    
    try:
        with open(resume_file, 'rb') as f:
            files = {'file': (resume_file.name, f, mime_type)}
            data = {
                'api_key': API_KEY,
                'model_type': DEFAULT_MODEL_TYPE,
                'model': DEFAULT_MODEL
            }
            
            print("Sending request...")
            print("⏳ This may take a while for PDF processing...")
            print(f"Using model: {DEFAULT_MODEL_TYPE}/{DEFAULT_MODEL}")
            
            # Try with a longer timeout and chunked upload
            response = requests.post(f"{API_BASE_URL}/extract-resume-json", 
                                   files=files, data=data, 
                                   timeout=300,  # 5 minutes
                                   stream=False)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Success!")
                print(f"Text length: {result.get('extracted_text_length', 0)}")
                
                # Debug: Show full response structure
                print(f"Response keys: {list(result.keys())}")
                
                if 'resume_json' in result:
                    resume_json = result['resume_json']
                    if resume_json:
                        print("Resume JSON structure:", list(resume_json.keys()))
                        
                        # Show some sample data
                        if 'basics' in resume_json:
                            basics = resume_json['basics']
                            print(f"Name: {basics.get('name', 'N/A')}")
                            print(f"Email: {basics.get('email', 'N/A')}")
                        
                        # Save to file for inspection
                        output_file = Path("debug_resume.json")
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(resume_json, f, indent=2, ensure_ascii=False)
                        print(f"Resume JSON saved to: {output_file}")
                    else:
                        print("⚠️  Resume JSON is empty or None")
                        print(f"Raw resume_json value: {resume_json}")
                else:
                    print("⚠️  No 'resume_json' key in response")
                    print(f"Available response data: {result}")
            else:
                print("✗ Error:")
                try:
                    error_response = response.json()
                    print(f"Error message: {error_response.get('error', 'Unknown error')}")
                    if 'traceback' in error_response:
                        print("Traceback (last 3 lines):")
                        traceback_lines = error_response['traceback'].split('\n')[-4:-1]
                        for line in traceback_lines:
                            if line.strip():
                                print(f"  {line}")
                except:
                    print(response.text)
                
    except requests.exceptions.Timeout:
        print("✗ Request timed out. The server might be taking too long to process the file.")
        print("   Try with a smaller file or check server logs.")
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {str(e)}")
        print("   The server might have crashed or stopped responding.")
        print("   Check the Flask server console for error messages.")
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_text_extraction_only():
    """Test just the text extraction to see what we're getting"""
    print("\nTesting text extraction quality...")
    
    resume_files = list(SAMPLE_FOLDER.glob("*.pdf"))
    if not resume_files:
        print("No PDF files found")
        return
    
    resume_file = resume_files[0]
    
    # Let's manually extract text to see what we get
    from doc_utils import extract_text_from_upload
    
    try:
        with open(resume_file, 'rb') as f:
            # Create a simple file-like object to mimic FileStorage
            class MockFile:
                def __init__(self, file_obj, filename):
                    self.file_obj = file_obj
                    self.filename = filename
                    self.content_type = 'application/pdf'
                
                def read(self):
                    return self.file_obj.read()
                
                def seek(self, pos):
                    return self.file_obj.seek(pos)
            
            mock_file = MockFile(f, resume_file.name)
            text = extract_text_from_upload(mock_file)
            
            print(f"Extracted text length: {len(text)}")
            print("First 500 characters:")
            print("-" * 50)
            print(text[:500])
            print("-" * 50)
            print("Last 500 characters:")
            print(text[-500:])
            print("-" * 50)
            
            # Save extracted text for manual inspection
            text_file = Path("extracted_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Full extracted text saved to: {text_file}")
            
            # Check if text looks like a resume
            keywords = ['experience', 'education', 'skills', 'work', 'university', 'college', 'degree', 'email', 'phone']
            found_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
            print(f"Resume keywords found: {found_keywords}")
            
            if len(found_keywords) < 3:
                print("⚠️  This might not be a proper resume or the text extraction is poor")
            
    except Exception as e:
        print(f"Error in text extraction: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    print("=" * 50)
    print("GenApply API Debug Test")
    print("=" * 50)
    print(f"Using API: {API_BASE_URL}")
    print(f"Using model: {DEFAULT_MODEL_TYPE}/{DEFAULT_MODEL}")
    print(f"Using API key: {API_KEY[:5]}...{API_KEY[-4:]}")
    print("=" * 50)
    
    # Step 1: Check if API is alive
    if not test_health_first():
        print("\n❌ API is not responding. Make sure the Flask server is running:")
        print("   python api.py")
        return
    
    # Step 1.5: Check text extraction quality
    test_text_extraction_only()
    
    # Step 2: Test with simple text file
    if test_with_smaller_file():
        print("\n✓ Basic text processing works!")
    else:
        print("\n❌ Basic text processing failed. Check API logs.")
        return
    
    # Step 3: Test with actual PDF file
    test_file_upload_debug()

if __name__ == "__main__":
    main()
