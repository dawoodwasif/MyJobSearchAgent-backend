from openai import OpenAI
import json

SYSTEM_PROMPT = "You are a smart assistant to career advisors at the Harvard Extension School. You will reply with JSON only."

CV_TEXT_PLACEHOLDER = "<CV_TEXT>"

SYSTEM_TAILORING = """
You are a smart assistant to career advisors at the Harvard Extension School. Your task is to rewrite
resumes to be more brief and convincing according to the Resumes and Cover Letters guide.
"""

TAILORING_PROMPT = """
Consider the following CV:
<CV_TEXT>

Your task is to rewrite the given CV. Follow these guidelines:
- Be truthful and objective to the experience listed in the CV
- Be specific rather than general
- Rewrite job highlight items using STAR methodology (but do not mention STAR explicitly)
- Fix spelling and grammar errors
- Write to express not impress
- Articulate and don't be flowery
- Prefer active voice over passive voice
- Do not include a summary about the candidate

Improved CV:
"""

BASICS_PROMPT = """
You are going to write a JSON resume section for an applicant applying for job posts.

Consider the following CV:
<CV_TEXT>

Now consider the following TypeScript Interface for the JSON schema:

interface Basics {
    name: string;
    email: string;
    phone: string;
    website: string;
    address: string;
}

Write the basics section according to the Basic schema. On the response, include only the JSON.
"""

EDUCATION_PROMPT = """
You are going to write a JSON resume section for an applicant applying for job posts.

Consider the following CV:
<CV_TEXT>

Now consider the following TypeScript Interface for the JSON schema:

interface EducationItem {
    institution: string;
    area: string;
    additionalAreas: string[];
    studyType: string;
    startDate: string;
    endDate: string;
    score: string;
    location: string;
}

interface Education {
    education: EducationItem[];
}

Write the education section according to the Education schema. On the response, include only the JSON.
"""

AWARDS_PROMPT = """
You are going to write a JSON resume section for an applicant applying for job posts.

Consider the following CV:
<CV_TEXT>

Now consider the following TypeScript Interface for the JSON schema:

interface AwardItem {
    title: string;
    date: string;
    awarder: string;
    summary: string;
}

interface Awards {
    awards: AwardItem[];
}

Write the awards section according to the Awards schema. Include only the awards section. On the response, include only the JSON.
"""

PROJECTS_PROMPT = """
You are going to write a JSON resume section for an applicant applying for job posts.

Consider the following CV:
<CV_TEXT>

Now consider the following TypeScript Interface for the JSON schema:

interface ProjectItem {
    name: string;
    description: string;
    keywords: string[];
    url: string;
}

interface Projects {
    projects: ProjectItem[];
}

Write the projects section according to the Projects schema. Include all projects, but only the ones present in the CV. On the response, include only the JSON.
"""

SKILLS_PROMPT = """
You are going to write a JSON resume section for an applicant applying for job posts.

Consider the following CV:
<CV_TEXT>

type HardSkills = "Programming Languages" | "Tools" | "Frameworks" | "Computer Proficiency";
type SoftSkills = "Team Work" | "Communication" | "Leadership" | "Problem Solving" | "Creativity";
type OtherSkills = string;

Now consider the following TypeScript Interface for the JSON schema:

interface SkillItem {
    name: HardSkills | SoftSkills | OtherSkills;
    keywords: string[];
}

interface Skills {
    skills: SkillItem[];
}

Write the skills section according to the Skills schema. Include only up to the top 4 skill names that are present in the CV and related with the education and work experience. On the response, include only the JSON.
"""

WORK_PROMPT = """
You are going to write a JSON resume section for an applicant applying for job posts.

Consider the following CV:
<CV_TEXT>

Now consider the following TypeScript Interface for the JSON schema:

interface WorkItem {
    company: string;
    position: string;
    startDate: string;
    endDate: string;
    location: string;
    highlights: string[];
}

interface Work {
    work: WorkItem[];
}

Write a work section for the candidate according to the Work schema. Include only the work experience and not the project experience. For each work experience, provide a company name, position name, start and end date, and bullet point for the highlights. Follow the Harvard Extension School Resume guidelines and phrase the highlights with the STAR methodology
"""


def generate_json_resume(cv_text, api_key, model="gpt-4o", model_type="OpenAI"):
    """Generate a JSON resume from a CV text"""
    print(f"DEBUG: Starting JSON resume generation with model: {model}, type: {model_type}")
    print(f"DEBUG: CV text length: {len(cv_text)}")
    print(f"DEBUG: First 200 chars of CV: {cv_text[:200]}...")
    
    sections = []
    print("DEBUG: Initializing OpenAI client")
    client = OpenAI(api_key=api_key)

    prompts = [
        ("BASICS", BASICS_PROMPT),
        ("EDUCATION", EDUCATION_PROMPT),
        ("AWARDS", AWARDS_PROMPT),
        ("PROJECTS", PROJECTS_PROMPT),
        ("SKILLS", SKILLS_PROMPT),
        ("WORK", WORK_PROMPT),
    ]

    for prompt_name, prompt in prompts:
        print(f"DEBUG: Processing {prompt_name} section...")
        
        filled_prompt = prompt.replace(CV_TEXT_PLACEHOLDER, cv_text)
        print(f"DEBUG: Filled prompt length for {prompt_name}: {len(filled_prompt)}")
        
        try:
            print(f"DEBUG: Making OpenAI API call for {prompt_name}...")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": filled_prompt},
                ],
            )
            answer = response.choices[0].message.content
            print(f"DEBUG: OpenAI response received for {prompt_name}, length: {len(answer)}")
            
            print(f"DEBUG: Raw response for {prompt_name}: {answer[:200]}...")
            
            # Clean up the response
            answer = answer.strip()
            if answer.startswith("```json"):
                answer = answer[7:]
            if answer.endswith("```"):
                answer = answer[:-3]
            answer = answer.strip()
            
            print(f"DEBUG: Cleaned response for {prompt_name}: {answer[:200]}...")
            
            # Parse JSON
            parsed_answer = json.loads(answer)
            print(f"DEBUG: Successfully parsed JSON for {prompt_name}")
            print(f"DEBUG: Parsed keys for {prompt_name}: {list(parsed_answer.keys())}")

            # Fix common GPT mistake for basics section
            if prompt_name == "BASICS" and "basics" not in parsed_answer:
                print(f"DEBUG: Fixing basics section structure for {prompt_name}")
                parsed_answer = {"basics": parsed_answer}

            sections.append(parsed_answer)
            print(f"DEBUG: Added {prompt_name} section to results")

        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parsing error for {prompt_name}: {e}")
            print(f"DEBUG: Raw answer that failed to parse: {answer}")
            print(f"DEBUG: Skipping {prompt_name} section due to parsing error")
            continue
        except Exception as e:
            print(f"DEBUG: Error processing {prompt_name}: {str(e)}")
            print(f"DEBUG: Skipping {prompt_name} section due to error")
            continue

    print(f"DEBUG: Processed {len(sections)} sections successfully")
    
    # Combine all sections
    final_json = {}
    for section in sections:
        print(f"DEBUG: Merging section with keys: {list(section.keys())}")
        final_json.update(section)

    print(f"DEBUG: Final JSON keys: {list(final_json.keys())}")
    print(f"DEBUG: Final JSON structure summary:")
    for key, value in final_json.items():
        if isinstance(value, dict):
            print(f"  - {key}: dict with {len(value)} keys")
        elif isinstance(value, list):
            print(f"  - {key}: list with {len(value)} items")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    return final_json


def tailor_resume(cv_text, api_key, model="gpt-4o", model_type="OpenAI"):
    print(f"DEBUG: Starting resume tailoring with model: {model}, type: {model_type}")
    print(f"DEBUG: CV text length for tailoring: {len(cv_text)}")
    
    filled_prompt = TAILORING_PROMPT.replace("<CV_TEXT>", cv_text)
    print(f"DEBUG: Filled tailoring prompt length: {len(filled_prompt)}")
    
    print("DEBUG: Using OpenAI for resume tailoring")
    client = OpenAI(api_key=api_key)
    try:
        print("DEBUG: Making OpenAI API call for tailoring...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_TAILORING},
                {"role": "user", "content": filled_prompt},
            ],
        )
        answer = response.choices[0].message.content.strip().strip('"').strip("'").rstrip('.') + '.'
        print(f"DEBUG: OpenAI tailoring response received, length: {len(answer)}")
        print(f"DEBUG: Tailored text preview: {answer[:300]}...")
        return answer
    except Exception as e:
        print(f"DEBUG: OpenAI tailoring failed: {e}")
        print("DEBUG: Returning original CV text")
        return cv_text
