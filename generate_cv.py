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
    
    while current_attempt <= max_retries:
        logger.info(f"Attempt {current_attempt}: Tailoring profile for {max_pages} page(s)...")
        
        tailored_profile_dict = tailor_profile_for_job(job_description, raw_profile, max_pages)
        logger.debug(f"tailored profile dict: {json.dumps(tailored_profile_dict, default=str)}")
        safe_profile = sanitize_dict(tailored_profile_dict)
        
        pdf_path = generate_and_save_pdf(safe_profile, design_choice)
        
        actual_pages = get_pdf_page_count(pdf_path)
        
        if max_pages == None or actual_pages <= max_pages:
            logger.success(f"Success! CV generated is {actual_pages} page(s). Fits within limit of {"unlimited" if not max_pages else max_pages}.")
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
    # tailored_profile = {"name": "Kenneth Plum Toft", "contact": {"phone": "+45 26167063", "email": ""}, "address": {"city": "Copenhagen", "country": "Denmark"}, "websites": [], "summary": "Generative AI & Full-Stack Engineer and MSc Computer Science candidate specializing in AI, Algorithms, and Frontier LLM technologies. Proven expertise in translating cutting-edge AI research into scalable, enterprise-grade production systems, with a strong track record at Dictus deploying AI-powered features, RAG/GraphRAG architectures, and specialized LLMs for automated content generation. Adept at full-stack development (Python, C#, .NET, TypeScript, React), AI microservice integration, prompt engineering, and CI/CD pipeline management. Combines rapid prototyping skills with robust software engineering practices to bridge the gap between data science innovation and business impact. Passionate about leveraging cloud-native technologies, cross-functional collaboration, and continuous learning to deliver high-quality, patient-centric AI solutions in dynamic, multinational environments.", "jobs": [{"company": "Dictus", "title": "Software Developer", "start": "Aug 2023", "end": "Present", "highlights": ["Spearheaded AI feature development for enterprise applications, including LLM-powered resume generation with advanced prompt engineering and pre/post-model processing.", "Designed and deployed speaker diarization & ASR systems for real-time audio analytics, optimizing model performance for production workloads.", "Built robust full-stack applications using C#/.NET and React/TypeScript, seamlessly integrated with Python-based AI microservices.", "Managed CI/CD pipelines (Docker, Jenkins, Git) for seamless remote server deployment and continuous delivery.", "Collaborated with cross-functional teams to deliver, maintain, and scale large-scale applications for the Norwegian Parliament (Stortinget)."]}, {"company": "Dictus", "title": "Software Developer Intern", "start": "Aug 2022", "end": "Aug 2023", "highlights": ["Developed a full-stack crowdsourcing platform for audio data collection and management using C#, .NET, Python, TypeScript, and React.", "Implemented AI-driven ASR and speaker separation pipelines using deep learning models to enhance audio processing capabilities.", "Contributed to end-to-end feature development, from backend API design to frontend UI implementation in an agile environment.", "Gained hands-on experience in deploying AI-integrated applications and collaborating with data science teams."]}, {"company": "Tradir.io", "title": "Software Engineer", "start": "Dec 2020", "end": "Aug 2021", "highlights": ["Engineered scalable CRM backend services in a fast-paced agile environment.", "Integrated third-party APIs (Mailgun, Nylas, Nanonets) to extend platform functionality and automate workflows.", "Developed RESTful APIs using Python (Django-REST) and PostgreSQL, deployed on AWS infrastructure.", "Collaborated with product and engineering teams to deliver reliable, high-performance software solutions."]}, {"company": "Greenwood Engineering", "title": "Student Worker", "start": "Aug 2021", "end": "Sep 2022", "highlights": ["Architected and maintained virtual machine environments for internal development tools (Git, Jenkins, Wiki).", "Managed server lifecycle, provisioning, and recycling to optimize infrastructure costs and performance.", "Provided enterprise IT support, ensuring system reliability and user productivity across the organization."]}, {"company": "Widex", "title": "Firmware Updater (Intern)", "start": "May 2018", "end": "Jul 2018", "highlights": ["Updated and validated firmware on newly manufactured hearing aid devices.", "Ensured compliance with quality standards and optimized device functionality for clinical use."]}, {"company": "Power", "title": "IT-Support (Part-time)", "start": "May 2018", "end": "Jul 2018", "highlights": ["Provided comprehensive IT support, including device configuration, troubleshooting, and data recovery.", "Delivered customer service for hardware and software issues across multiple device ecosystems."]}], "projects": [{"name": "Master's Thesis: Synergy Effects of GraphRAG, Fine-tuned Embeddings, and Specialized LLMs on Automated Content Generation", "role": "Researcher & Developer", "start": "2024", "end": "2026", "highlights": ["Conducting advanced research on the synergy between GraphRAG, fine-tuned embeddings, and specialized LLMs for automated content generation.", "Developing a full-stack benchmarking application to evaluate generation quality against standard baselines.", "Implementing knowledge graph-enhanced retrieval, model fine-tuning, and deployment pipelines for production readiness.", "Directly addressing industry challenges in cost-optimized model inference and technical framework selection for high-fidelity generative outputs."]}], "education": [{"degree": "MSc AI and Algorithms", "institution": "Technical University of Denmark", "start_date": "2024", "end_date": "2026", "description": "Specializing in Generative AI, RAG/GraphRAG architectures, and advanced algorithms. Master's Thesis focuses on synergies between specialized LLMs, fine-tuned embeddings, and automated content generation. Developing full-stack benchmarking tools, implementing retrieval pipelines, and optimizing model usage costs for enterprise applications."}, {"degree": "BSc Computer Engineering", "institution": "Technical University of Denmark", "start_date": "2019", "end_date": "2023", "description": "Comprehensive program covering software engineering, algorithms, systems architecture, and data structures. Developed strong foundations in full-stack development, cloud computing, and AI integration."}, {"degree": "Exchange Program in Computer Science", "institution": "Hanyang University", "start_date": "2020", "end_date": "2021", "description": "International exchange focused on advanced computer science curricula, cross-cultural collaboration, and exposure to diverse academic and technical environments."}], "courses": [], "patents": [], "skills": ["C#", "Python", "TypeScript", "JavaScript", "Java", "C", "SQL", "ASP.NET", ".NET", "Django REST", "FastAPI", "Node.js", "PyTorch", "Scikit-Learn", "HuggingFace", "Docker", "Git", "Jenkins", "AWS", "Google Cloud Platform", "DVC", "RabbitMQ", "WandB", "PostgreSQL", "MySQL", "LLMs", "Prompt Engineering", "RAG", "GraphRAG", "ASR", "Speaker Diarization", "Speaker Separation", "Deep Learning", "CI/CD", "API Integration", "Agile Development", "Microservices Architecture", "Cloud-Native Deployment", "Vector Databases", "Frontend/Backend Development", "System Design", "Technical Documentation"], "languages": [{"name": "English", "proficiency": "Professional Working Proficiency"}, {"name": "Korean", "proficiency": "Low Intermediate"}, {"name": "Danish", "proficiency": "Native"}], "publications": [], "honors": []}
    tailored_profile = {"name": "Kenneth Plum Toft", "contact": {"phone": "+45 26167063", "email": ""}, "address": {"city": "Copenhagen", "country": "Denmark"}, "websites": [], "summary": "Generative AI & Full-Stack Engineer currently pursuing an MSc in Computer Science (AI and Algorithms) with a specialized focus on frontier AI technologies, including RAG, GraphRAG, and specialized LLMs. Proven track record in architecting and deploying enterprise-grade AI solutions, taking complex AI-centric use-cases from ideation to production. Expert in full-stack development (C#/.NET, Python, React/TypeScript) and cloud-native infrastructure (Docker, Jenkins, AWS), with extensive experience in CI/CD pipelines, scalable microservices, and model optimization. A highly self-motivated collaborator with exceptional communication skills, passionate about leveraging cutting-edge AI to drive business impact, streamline workflows, and deliver high-quality products in dynamic, multinational environments.", "jobs": [{"company": "Dictus", "title": "Software Developer", "start": "Aug 2023", "end": "Present", "highlights": ["Spearheaded the design and production deployment of AI-powered features, including a resume generation tool leveraging modern LLMs.", "Implemented advanced prompt engineering and developed robust pre/post-processing pipelines for seamless model invocation.", "Built scalable microservices integrating Python-based AI models with C#/.NET and React (TypeScript) frontend architectures.", "Integrated speaker diarization and Whisper/Wav2Vec models, optimizing performance for real-world audio processing.", "Managed end-to-end CI/CD pipelines using Docker, Git, and Jenkins on remote cloud servers.", "Collaborated with cross-functional teams to maintain and scale large-scale enterprise applications for Stortinget, ensuring high-quality deliverables."]}, {"company": "Dictus", "title": "Software Developer Intern", "start": "Aug 2022", "end": "Aug 2023", "highlights": ["Engineered a full-stack web platform for crowdsourcing audio data using C#/.NET, Python, and React (TypeScript).", "Developed and deployed deep learning models for Automatic Speech Recognition (ASR) and speaker separation.", "Applied modern software development practices and agile methodologies to deliver production-ready AI integrations.", "Managed rapid prototyping and iteration cycles, aligning technical deliverables with stakeholder requirements."]}, {"company": "Greenwood Engineering", "title": "Student Worker", "start": "Aug 2021", "end": "Sep 2022", "highlights": ["Provisioned, maintained, and optimized physical and virtual server infrastructure for enterprise use.", "Built and managed VM hosts for internal development and CI/CD tools (Git, Jenkins, Wiki).", "Provided enterprise IT support and streamlined server lifecycle management processes."]}, {"company": "Tradir.io", "title": "Software Engineer", "start": "Dec 2020", "end": "Aug 2021", "highlights": ["Developed and maintained backend CRM software in an agile environment using Python, Django-REST, and PostgreSQL.", "Integrated third-party APIs (Mailgun, Nylas, Nanonets) to streamline workflow automation and data processing.", "Deployed solutions on AWS, ensuring scalable and secure backend architecture."]}, {"company": "Widex", "title": "Firmware Updater", "start": "Feb 2019", "end": "Oct 2019", "highlights": ["Executed precision firmware updates on newly manufactured hearing aid devices, ensuring regulatory compliance and device reliability.", "Collaborated with hardware and engineering teams to validate firmware deployment processes."]}, {"company": "Power", "title": "IT-Support", "start": "Sep 2016", "end": "Oct 2017", "highlights": ["Provided comprehensive IT support for end-user devices including computers, smartphones, tablets, and smartwatches.", "Managed data transfer, recovery, and customer service operations with a focus on rapid resolution."]}], "projects": [{"name": "Audio Transcription & Speaker Separation Platform", "role": "Developer", "start": "2022", "end": "2023", "highlights": ["Architected a full-stack application for automated audio transcription using ASR and deep learning-based speaker separation.", "Deployed production-ready AI models integrating front-end React UI with Python backend services.", "Continuously iterated on the platform post-launch, maintaining active development and commercial deployment."]}], "education": [{"degree": "MSc in AI and Algorithms", "institution": "Technical University of Denmark", "start_date": "2024", "end_date": "2026", "description": "Master's Thesis: Synergy Effects of GraphRAG, Fine-tuned Embeddings, and Specialized LLMs on Automated Content Generation. Developing a full-stack application to benchmark automated generation quality against standard baselines. Implementing and deploying advanced RAG architectures, GraphRAG techniques, and fine-tuned specialized LLMs."}, {"degree": "BSc in Computer Engineering", "institution": "Technical University of Denmark", "start_date": "2019", "end_date": "2023", "description": "Comprehensive undergraduate studies in computer engineering, focusing on software development, systems architecture, algorithmic problem-solving, and full-stack engineering principles."}, {"degree": "Exchange Student in Computer Science", "institution": "Hanyang University (South Korea)", "start_date": "2020", "end_date": "2021", "description": "International academic exchange program specializing in advanced computer science concepts, software engineering methodologies, and cross-cultural technical collaboration."}], "courses": [], "patents": [], "skills": ["C#", "Jenkins", "ASP.NET", ".NET", "SQL", "Python", "TypeScript", "JavaScript", "MySQL", "PostgreSQL", "Docker", "Git", "React", "AWS", "Google Cloud Platform", "Java", "DVC", "RabbitMQ", "HuggingFace", "Scikit-Learn", "Django REST", "WandB", "FastAPI", "Node.js", "C", "PyTorch", "LLMs", "RAG", "GraphRAG", "Prompt Engineering", "Speaker Diarization", "ASR", "Deep Learning", "CI/CD", "Agile Development", "Enterprise Software Architecture", "AI-to-Production Deployment", "Cross-functional Collaboration"], "languages": [{"name": "English", "proficiency": "Professional Working Proficiency"}, {"name": "Danish", "proficiency": "Native"}, {"name": "Korean", "proficiency": "Low Intermediate"}], "publications": [], "honors": []}
    logger.info("tailored profile: " + json.dumps(tailored_profile, default=str))
    safe_profile = sanitize_dict(tailored_profile)
    logger.info("safe profile: " + json.dumps(safe_profile, default=str))
    pdf_path = generate_and_save_pdf(safe_profile, 1)