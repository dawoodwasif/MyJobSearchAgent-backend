from openai import OpenAI
import google.generativeai as genai
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


def generate_json_resume(cv_text, api_key, model="deepseek-chat", model_type="DeepSeek"):
    """Generate a JSON resume from a CV text"""
    print(f"DEBUG: Starting JSON resume generation with model: {model}, type: {model_type}")
    print(f"DEBUG: CV text length: {len(cv_text)}")
    print(f"DEBUG: First 200 chars of CV: {cv_text[:200]}...")
    
    sections = []
    if model_type == "OpenAI":
        client = OpenAI(api_key=api_key)
    elif model_type == "DeepSeek":
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    elif model_type == "Gemini":
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)

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
        
        try:
            if model_type == "OpenAI":
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": filled_prompt},
                    ],
                )
                answer = response.choices[0].message.content
            elif model_type == "DeepSeek":
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": filled_prompt},
                    ],
                )
                answer = response.choices[0].message.content
            elif model_type == "Gemini":
                full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {filled_prompt}\nAssistant:"
                response = model_instance.generate_content(full_prompt)
                answer = response.parts[0].text
                answer = answer.strip("'").replace("```json\n", "").replace("\n```", "")
            
            print(f"DEBUG: Raw response for {prompt_name}: {answer[:200]}...")
            
            # Clean up the response
            answer = answer.strip()
            if answer.startswith("```json"):
                answer = answer[7:]
            if answer.endswith("```"):
                answer = answer[:-3]
            answer = answer.strip()
            
            # Parse JSON
            parsed_answer = json.loads(answer)
            
            # Fix common GPT mistake for basics section
            if prompt_name == "BASICS" and "basics" not in parsed_answer:
                parsed_answer = {"basics": parsed_answer}
            
            print(f"DEBUG: Successfully parsed {prompt_name} section: {list(parsed_answer.keys())}")
            sections.append(parsed_answer)
            
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parsing error for {prompt_name}: {e}")
            print(f"DEBUG: Raw answer was: {answer}")
            # Continue with other sections even if one fails
            continue
        except Exception as e:
            print(f"DEBUG: Error processing {prompt_name}: {str(e)}")
            continue

    # Combine all sections
    final_json = {}
    for section in sections:
        final_json.update(section)
    
    print(f"DEBUG: Final JSON keys: {list(final_json.keys())}")
    return final_json


def tailor_resume(cv_text, api_key, model="deepseek-chat", model_type="DeepSeek"):
    filled_prompt = TAILORING_PROMPT.replace("<CV_TEXT>", cv_text)
    if model_type == "OpenAI":
        client = OpenAI(api_key=api_key)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_TAILORING},
                    {"role": "user", "content": filled_prompt},
                ],
            )
            answer = response.choices[0].message.content.strip().strip('"').strip("'").rstrip('.') + '.'
            return answer
        except Exception as e:
            print(e)
            print("Failed to tailor resume.")
            return cv_text
    elif model_type == "DeepSeek":
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_TAILORING},
                    {"role": "user", "content": filled_prompt},
                ],
            )
            answer = response.choices[0].message.content.strip().strip('"').strip("'").rstrip('.') + '.'
            return answer
        except Exception as e:
            print(e)
            print("Failed to tailor resume with DeepSeek.")
            return cv_text
    elif model_type == "Gemini":
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)
        try:
            full_prompt = f"{SYSTEM_TAILORING}\n\nUser: {filled_prompt}\nAssistant:"
            response = model_instance.generate_content(full_prompt)
            answer = response.parts[0].text
            return answer
        except Exception as e:
            print(e)
            print("Failed to tailor resume.")
            return cv_text
