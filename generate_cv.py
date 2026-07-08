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

def tailor_profile_for_job(job_description: str, raw_profile: dict, max_pages: int = None) -> dict:
    prompt = f"""
    You are an expert CV writer. Tailor the candidate's raw data to the Job Description to create a fully comprehensive CV.
    
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
        "languages": ["Lang 1", "Lang 2"],
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

def generate_tailored_cv(job_description: str, candidate_name: str, design_choice: int = 4, max_pages: int = 1):
    logger.info(f"Retrieving graph data for {candidate_name}...")
    raw_profile = get_candidate_profile(candidate_name)
    
    max_retries = 2
    current_attempt = 1
    
    while current_attempt <= max_retries:
        logger.info(f"Attempt {current_attempt}: Tailoring profile for {max_pages} page(s)...")
        
        # 1. Map data with LLM
        tailored_profile_dict = tailor_profile_for_job(job_description, raw_profile, max_pages)
        safe_profile = sanitize_dict(tailored_profile_dict)
        
        # 2. Compile LaTeX
        pdf_path = generate_and_save_pdf(safe_profile, design_choice)
        
        # 3. Check page count
        actual_pages = get_pdf_page_count(pdf_path)
        
        if actual_pages <= max_pages:
            logger.success(f"Success! CV generated is {actual_pages} page(s). Fits within limit of {max_pages}.")
            return pdf_path
        else:
            logger.warning(f"CV generated {actual_pages} pages. Exceeds limit of {max_pages}.")
            # TODO:
            # If we fail, we could append an error to the LLM messages for the next loop:
            # "Your previous output resulted in a PDF that was too long. You MUST cut 20% of the content."
            current_attempt += 1

    logger.error("Could not fit CV into the specified page limit after max retries.")
    return pdf_path


if __name__ == "__main__":
    target_job = "We are looking for a Software Developer with experience in backend systems, Python, and Docker."
    
    tailored_profile = {"name": "Kenneth Plum Toft", "contact": {"phone": "+45 26167063", "email": ""}, "address": {"city": "Copenhagen", "country": "Denmark"}, "websites": [], "summary": "Generative AI & Full-Stack Engineer with a Master\u2019s focus on AI and Algorithms, specializing in translating frontier AI technologies into scalable, production-ready solutions. Proven expertise in LLM integration, RAG/GraphRAG architectures, and automated content generation, complemented by robust full-stack development skills in Python, C#/.NET, and React/TypeScript. Adept at managing end-to-end software lifecycles, including CI/CD, Docker containerization, and cloud infrastructure. Recognized for bridging the gap between AI research and enterprise product deployment, fostering cross-functional collaboration, and delivering high-quality, mission-driven software applications in dynamic, multinational environments.", "jobs": [{"company": "Dictus", "title": "Software Developer", "start": "Aug 2023", "end": "Present", "highlights": ["Architected and deployed AI-powered features from ideation to production, including an LLM-driven resume generator and advanced speaker diarization/ASR systems.", "Developed enterprise-grade full-stack applications using C#/.NET, React (TypeScript), and Python microservices, ensuring seamless integration and high performance.", "Optimized prompt engineering workflows and implemented pre/post-model invocation processing to enhance output quality and reduce computational overhead.", "Managed CI/CD pipelines and containerized deployments using Docker, Jenkins, and Git, supporting large-scale projects for national government entities."]}, {"company": "Dictus", "title": "Software Developer Intern", "start": "Aug 2022", "end": "Aug 2023", "highlights": ["Built a full-stack web platform for crowdsourcing audio data, enabling scalable data collection for AI training pipelines.", "Developed transcription and speaker separation applications leveraging deep learning models and ASR technologies.", "Engineered backend services in C#/.NET and Python, with a frontend built in TypeScript and React.", "Collaborated with domain experts to translate AI research concepts into functional, user-facing prototypes."]}, {"company": "Greenwood Engineering", "title": "Student Worker", "start": "Aug 2021", "end": "Sep 2022", "highlights": ["Provisioned and maintained on-premise servers and virtual machines hosting Git, Wiki, and Jenkins CI/CD pipelines.", "Automated server provisioning and lifecycle management to support internal development workflows.", "Provided technical support and documentation to streamline engineering team operations."]}, {"company": "Tradir.io", "title": "Software Engineer", "start": "Dec 2020", "end": "Aug 2021", "highlights": ["Developed CRM software backend in agile environments, focusing on scalable API integrations (Mailgun, Nylas, Nanonets).", "Managed PostgreSQL databases and deployed solutions on AWS cloud infrastructure.", "Implemented RESTful services using Django-REST and Python, improving data workflow efficiency."]}, {"company": "Power", "title": "IT-Support", "start": "May 2018", "end": "Jul 2018", "highlights": ["Delivered customer-facing IT support for hardware troubleshooting, device configuration, and data recovery.", "Managed troubleshooting for computers, mobile devices, and peripherals in a fast-paced retail environment."]}, {"company": "Widex", "title": "Firmware Updater", "start": "May 2018", "end": "Jul 2018", "highlights": ["Performed precision firmware updates on newly manufactured hearing aid devices.", "Ensured quality control and device functionality alignment with manufacturing specifications."]}], "projects": [{"name": "Master's Thesis: Synergy Effects of GraphRAG, Fine-tuned Embeddings, and Specialized LLMs on Automated Content Generation", "role": "Researcher & Developer", "start": "2024", "end": "2026", "highlights": ["Designing and benchmarking a full-stack evaluation framework to compare generative AI outputs against standard baselines.", "Implementing advanced RAG and GraphRAG architectures, integrating knowledge graphs with retrieval-augmented generation pipelines.", "Fine-tuning and deploying specialized LLMs to optimize model usage costs while maintaining high-fidelity generative outputs.", "Addressing critical challenges in AI framework selection and infrastructure optimization for scalable content automation."]}], "education": [{"degree": "AI and Algorithms (MSc)", "institution": "Technical University of Denmark", "start_date": "2024", "end_date": "2026", "description": "Advanced research in RAG, GraphRAG, and specialized LLMs for automated content generation. Developing full-stack benchmarks for AI quality evaluation and optimizing infrastructure for scalable, cost-effective generative models."}, {"degree": "Computer Engineering (BSc)", "institution": "Technical University of Denmark", "start_date": "2019", "end_date": "2023", "description": "Comprehensive foundation in software engineering, algorithms, and systems architecture with a focus on modern development practices and AI readiness."}, {"degree": "Computer Science (Exchange)", "institution": "Hanyang University", "start_date": "2020", "end_date": "2021", "description": "International exchange program focused on advanced software development and cross-cultural technical collaboration."}], "courses": [], "patents": [], "skills": ["Python", "C#", "TypeScript", "JavaScript", "React", "ASP.NET/.NET", "FastAPI", "Django REST", "PyTorch", "HuggingFace", "Scikit-Learn", "DVC", "Docker", "AWS", "Google Cloud Platform", "PostgreSQL", "MySQL", "Git", "Jenkins", "CI/CD", "LLMs", "RAG", "GraphRAG", "Prompt Engineering", "Speaker Diarization", "ASR", "Deep Learning", "Vector Databases", "Semantic Search", "Agile Development"], "languages": ["English", "Korean", "Danish"], "publications": [], "honors": []}
    logger.info("tailored profile: " + json.dumps(tailored_profile, default=str))
    safe_profile = sanitize_dict(tailored_profile)
    logger.info("safe profile: " + json.dumps(safe_profile, default=str))
    pdf_path = generate_and_save_pdf(safe_profile, 1)