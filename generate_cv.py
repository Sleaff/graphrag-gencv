import subprocess
import json
from loguru import logger
from pypdf import PdfReader

from llm_service import ChatMessage, call_llm
from query_graph import get_candidate_profile
from pdf_service import generate_and_save_pdf

def get_pdf_page_count(pdf_path: str) -> int:
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        logger.error(f"Could not read PDF to verify page count: {e}")

def get_length_rules(max_pages: int) -> str:
    if max_pages == 1:
        return """
        - EXTREME BREVITY REQUIRED: The final CV MUST fit on a single page.
        - Summary: Maximum of 2 short sentences.
        - Work Experience: Include ONLY the 2-3 most recent or highly relevant jobs. 
        - Highlights (Bullet Points): STRICT maximum of 3 bullet points per job/project. Keep them to a single line each.
        - Skills: Filter down to the top 8-10 most critical skills matching the job description.
        - Education: Omit descriptions entirely. Just list the degree, institution, and dates.
        - Optional Sections: Completely omit 'courses', 'patents', 'honors', and 'publications' unless they are the absolute primary selling point for this specific role.
        """
    elif max_pages == 2:
        return """
        - STANDARD LENGTH: The final CV should span optimally across 2 pages.
        - Summary: Provide a well-rounded paragraph of 3-4 sentences.
        - Work Experience: Include up to 4-5 relevant roles.
        - Highlights (Bullet Points): Up to 4-5 bullet points for recent/major roles, and 2-3 for older roles.
        - Skills: Include up to 15-20 relevant skills.
        - Education & Projects: Include brief 1-2 sentence descriptions or highlights.
        - Optional Sections: Include 'courses', 'patents', and 'publications' if they add direct value to the job application, but keep them concise.
        """
    else:
        return """
        - COMPREHENSIVE ACADEMIC/EXECUTIVE CV: Length is not restricted.
        - Summary: Write a comprehensive professional narrative detailing expertise and career trajectory.
        - Work Experience: Include the full relevant work history. Major roles can have many detailed bullet points.
        - Skills: Provide an exhaustive list of all technical, language, and professional skills.
        - Education & Projects: Provide full details, descriptions, and highlights for all academic and project work.
        - Optional Sections: Include ALL 'publications', 'patents', 'honors', and 'courses'. Do not omit any achievements.
        """

def tailor_profile_for_job(job_description: str, raw_profile: dict, max_pages: int = None, error_feedback: str = "") -> dict:
    feedback_prompt = ""
    if error_feedback:
        feedback_prompt = f"""
        CRITICAL WARNING FROM PREVIOUS ATTEMPT: 
        {error_feedback}
        You MUST correct this issue in your new response.
        """

    prompt = f"""
    You are an expert CV writer. Tailor the candidate's raw data to the Job Description to create a fully comprehensive CV.
    
    {feedback_prompt}
    
    CRITICAL LENGTH CONSTRAINTS:
    {get_length_rules(max_pages)}

    1. Filter out completely irrelevant data, but ensure major sections (Projects, Courses, Patents, etc.) are included if they exist in the raw data.
    2. Rewrite 'description' fields in 'jobs' and 'projects' into concise, impactful arrays of bullet points ('highlights').
    3. Synthesize 'short_description' and 'long_description' into a single, polished 'summary' paragraph.
    
    Return a JSON object strictly following this structure:
    {{
        "name": "Candidate Name",
        "contact": {{"phone": "...", "email": "..."}},
        "address": {{"city": "City", "country": "Country"}},
        "websites": [{{"url": "...", "website_type": "..."}}],
        "summary": "Polished professional summary...",
        "jobs": [{{
            "company": "...", "title": "...", "start": "...", "end": "...", "highlights": ["...", "..."]
        }}],
        "projects": [{{
            "name": "...", "role": "...", "start": "...", "end": "...", "highlights": ["...", "..."]
        }}],
        "education": [{{"degree": "...", "institution": "...", "start_date": "...", "end_date": "...", "description": "..."}}],
        "courses": [{{"title": "...", "organized_by": "...", "date": "...", "has_certification": true}}],
        "patents": [{{"title": "...", "number": "...", "date": "...", "status": "..."}}],
        "skills": ["Skill 1", "Skill 2"], 
        "languages": [{{"name": "...", "proficiency": "..."}}],
        "publications": [{{"title": "...", "date": "..."}}],
        "honors": [{{"title": "...", "issuer": "...", "date": "..."}}]
    }}
    
    Raw Profile:
    {json.dumps(raw_profile, default=str)}
    
    Job Description:
    {job_description}
    """

    messages = [
        ChatMessage(role="system", content="You are a data mapper and CV expert. Output strictly valid JSON."),
        ChatMessage(role="user", content=prompt),
    ]

    result = call_llm(messages)
    try:
        return json.loads(result)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response into JSON: {e}")
        return raw_profile


def escape_latex(text: str) -> str:
    """Escapes characters that are special in LaTeX, preserving backslashes."""
    if not isinstance(text, str):
        return str(text)
    
    replacements = {
        r"#": r"\#",
        r"&": r"\&",
        r"%": r"\%",
        r"$": r"\$",
        r"_": r"\_",
        r"{": r"\{",
        r"}": r"\}",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

def sanitize_dict(d):
    """Recursively sanitize all strings in the dictionary/list."""
    if isinstance(d, dict):
        return {k: sanitize_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [sanitize_dict(i) for i in d]
    elif isinstance(d, str):
        return escape_latex(d)
    return d

def generate_tailored_cv(job_description: str, candidate_name: str, design_choice: int = 1, max_pages: int | None = None):
    logger.info(f"Retrieving graph data for {candidate_name}...")
    raw_profile = get_candidate_profile(candidate_name)
    logger.debug(f"Raw profile data: {json.dumps(raw_profile, default=str)}")
    
    max_retries = 3
    current_attempt = 1
    error_feedback = ""
    last_successful_pdf = None
    
    while current_attempt <= max_retries:
        logger.info(f"Attempt {current_attempt}/{max_retries}: Tailoring profile...")
        
        tailored_profile_dict = tailor_profile_for_job(job_description, raw_profile, max_pages, error_feedback)
        logger.debug(f"Tailored profile data: {json.dumps(tailored_profile_dict, default=str)}")
        safe_profile = sanitize_dict(tailored_profile_dict)
        logger.debug(f"Sanitized profile data: {json.dumps(safe_profile, default=str)}")
        
        try:
            pdf_path = generate_and_save_pdf(safe_profile, design_choice)
            last_successful_pdf = pdf_path # save it in case future attempts fail
        except subprocess.CalledProcessError as e:
            logger.error(f"LaTeX Compilation failed on attempt {current_attempt}.")
            logger.debug(f"Error details: {e}")
            error_feedback = "Your previous output caused a fatal LaTeX compilation error. Ensure you are not including invalid characters or breaking the JSON schema."
            current_attempt += 1
            continue
        except Exception as e:
            logger.error(f"Unexpected error during PDF generation: {e}")
            logger.debug(f"Error details: {e}")
            error_feedback = f"An unexpected system error occurred: {str(e)}"
            current_attempt += 1
            continue

        actual_pages = get_pdf_page_count(pdf_path)
        
        if max_pages is None or actual_pages <= max_pages:
            logger.success(f"Success! CV generated is {actual_pages} page(s). Fits within limit.")
            return pdf_path
        else:
            logger.warning(f"CV generated {actual_pages} pages. Exceeds limit of {max_pages}.")
            error_feedback = f"Your previous output resulted in a {actual_pages}-page CV. You MUST cut down the text further to fit it into exactly {max_pages} page(s)."
            current_attempt += 1

    logger.error("Could not fit CV into the specified constraints after max retries.")
    
    if last_successful_pdf:
        logger.warning("Returning the last successfully compiled PDF despite it failing constraints.")
        return last_successful_pdf
    
    raise RuntimeError("CV generation failed completely after all retries.")


if __name__ == "__main__":
    tailored_profile = {"name": "Kenneth Plum Toft", "contact": {"phone": "+45 26167063", "email": "wowkenneth@gmail.com"}, "address": {"city": "Copenhagen", "country": "Denmark"}, "websites": [], "summary": "Generative AI & Full-Stack Engineer currently pursuing an MSc in Computer Science (AI and Algorithms) with a specialized focus on frontier AI technologies, including RAG, GraphRAG, and specialized LLMs. Proven track record in architecting and deploying enterprise-grade AI solutions, taking complex AI-centric use-cases from ideation to production. Expert in full-stack development (C#/.NET, Python, React/TypeScript) and cloud-native infrastructure (Docker, Jenkins, AWS), with extensive experience in CI/CD pipelines, scalable microservices, and model optimization. A highly self-motivated collaborator with exceptional communication skills, passionate about leveraging cutting-edge AI to drive business impact, streamline workflows, and deliver high-quality products in dynamic, multinational environments.", "jobs": [{"company": "Dictus", "title": "Software Developer", "start": "Aug 2023", "end": "Present", "highlights": ["Spearheaded the design and production deployment of AI-powered features, including a resume generation tool leveraging modern LLMs.", "Implemented advanced prompt engineering and developed robust pre/post-processing pipelines for seamless model invocation.", "Built scalable microservices integrating Python-based AI models with C#/.NET and React (TypeScript) frontend architectures.", "Integrated speaker diarization and Whisper/Wav2Vec models, optimizing performance for real-world audio processing.", "Managed end-to-end CI/CD pipelines using Docker, Git, and Jenkins on remote cloud servers.", "Collaborated with cross-functional teams to maintain and scale large-scale enterprise applications for Stortinget, ensuring high-quality deliverables."]}, {"company": "Dictus", "title": "Software Developer Intern", "start": "Aug 2022", "end": "Aug 2023", "highlights": ["Engineered a full-stack web platform for crowdsourcing audio data using C#/.NET, Python, and React (TypeScript).", "Developed and deployed deep learning models for Automatic Speech Recognition (ASR) and speaker separation.", "Applied modern software development practices and agile methodologies to deliver production-ready AI integrations.", "Managed rapid prototyping and iteration cycles, aligning technical deliverables with stakeholder requirements."]}, {"company": "Greenwood Engineering", "title": "Student Worker", "start": "Aug 2021", "end": "Sep 2022", "highlights": ["Provisioned, maintained, and optimized physical and virtual server infrastructure for enterprise use.", "Built and managed VM hosts for internal development and CI/CD tools (Git, Jenkins, Wiki).", "Provided enterprise IT support and streamlined server lifecycle management processes."]}, {"company": "Tradir.io", "title": "Software Engineer", "start": "Dec 2020", "end": "Aug 2021", "highlights": ["Developed and maintained backend CRM software in an agile environment using Python, Django-REST, and PostgreSQL.", "Integrated third-party APIs (Mailgun, Nylas, Nanonets) to streamline workflow automation and data processing.", "Deployed solutions on AWS, ensuring scalable and secure backend architecture."]}, {"company": "Widex", "title": "Firmware Updater", "start": "Feb 2019", "end": "Oct 2019", "highlights": ["Executed precision firmware updates on newly manufactured hearing aid devices, ensuring regulatory compliance and device reliability.", "Collaborated with hardware and engineering teams to validate firmware deployment processes."]}, {"company": "Power", "title": "IT-Support", "start": "Sep 2016", "end": "Oct 2017", "highlights": ["Provided comprehensive IT support for end-user devices including computers, smartphones, tablets, and smartwatches.", "Managed data transfer, recovery, and customer service operations with a focus on rapid resolution."]}], "projects": [{"name": "Audio Transcription & Speaker Separation Platform", "role": "Developer", "start": "2022", "end": "2023", "highlights": ["Architected a full-stack application for automated audio transcription using ASR and deep learning-based speaker separation.", "Deployed production-ready AI models integrating front-end React UI with Python backend services.", "Continuously iterated on the platform post-launch, maintaining active development and commercial deployment."]}], "education": [{"degree": "MSc in AI and Algorithms", "institution": "Technical University of Denmark", "start_date": "2024", "end_date": "2026", "description": "Master's Thesis: Synergy Effects of GraphRAG, Fine-tuned Embeddings, and Specialized LLMs on Automated Content Generation. Developing a full-stack application to benchmark automated generation quality against standard baselines. Implementing and deploying advanced RAG architectures, GraphRAG techniques, and fine-tuned specialized LLMs."}, {"degree": "BSc in Computer Engineering", "institution": "Technical University of Denmark", "start_date": "2019", "end_date": "2023", "description": "Comprehensive undergraduate studies in computer engineering, focusing on software development, systems architecture, algorithmic problem-solving, and full-stack engineering principles."}, {"degree": "Exchange Student in Computer Science", "institution": "Hanyang University (South Korea)", "start_date": "2020", "end_date": "2021", "description": "International academic exchange program specializing in advanced computer science concepts, software engineering methodologies, and cross-cultural technical collaboration."}], "courses": [], "patents": [], "skills": ["C#", "Jenkins", "ASP.NET", ".NET", "SQL", "Python", "TypeScript", "JavaScript", "MySQL", "PostgreSQL", "Docker", "Git", "React", "AWS", "Google Cloud Platform", "Java", "DVC", "RabbitMQ", "HuggingFace", "Scikit-Learn", "Django REST", "WandB", "FastAPI", "Node.js", "C", "PyTorch", "LLMs", "RAG", "GraphRAG", "Prompt Engineering", "Speaker Diarization", "ASR", "Deep Learning", "CI/CD", "Agile Development", "Enterprise Software Architecture", "AI-to-Production Deployment", "Cross-functional Collaboration"], "languages": [{"name": "English", "proficiency": "Professional Working Proficiency"}, {"name": "Danish", "proficiency": "Native"}, {"name": "Korean", "proficiency": "Low Intermediate"}], "publications": [], "honors": []}
    logger.info("tailored profile: " + json.dumps(tailored_profile, default=str))
    safe_profile = sanitize_dict(tailored_profile)
    logger.info("safe profile: " + json.dumps(safe_profile, default=str))
    pdf_path = generate_and_save_pdf(safe_profile, 1)