from datetime import datetime

headerCV = r"""
    \documentclass[letterpaper,11pt]{article}
    \usepackage[empty]{fullpage}
    
    % Modern Fonts
    \usepackage[sfdefault,light]{FiraSans} 
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage[]{babel}
    
    % Styling and Icons
    \usepackage{fontawesome}
    \usepackage[svgnames]{xcolor}
    \usepackage{hyperref}
    \usepackage{enumitem}

    % Define Modern Colors
    \definecolor{primary}{HTML}{1F2937} % Tailwind Gray 800 (Dark grey for main text/headers)
    \definecolor{accent}{HTML}{2563EB}  % Tailwind Blue 600 (Sleek professional blue)
    \definecolor{text}{HTML}{4B5563}    % Tailwind Gray 600 (Softer grey for descriptions)

    % Link Setup
    \hypersetup{colorlinks=true, urlcolor=accent}

    % Modern Margin Setup
    \addtolength{\oddsidemargin}{-0.5in}
    \addtolength{\evensidemargin}{-0.5in}
    \addtolength{\textwidth}{1.0in}
    \addtolength{\topmargin}{-0.5in}
    \addtolength{\textheight}{1.0in}
    \raggedbottom
    \raggedright
    \setlength{\tabcolsep}{0in}

    % Global List Styling (Tightens up the spacing and modernizes the bullets)
    \setlist[itemize]{leftmargin=*, itemsep=2pt, topsep=4pt, parsep=0pt}
    \setlist[itemize,1]{label=\color{accent}\faAngleRight} % Sleek chevron for primary bullets
    \setlist[itemize,2]{label=\color{accent}$\circ$, leftmargin=1em} % Hollow circles for sub-bullets

    %-----------------------------------------------------------
    % Custom Modern Commands
    
    % Standard list item with softer text color
    \newcommand{\resitem}[1]{\item \color{text}#1}
    
    % Sleek Header with underline instead of bulky box
    \newcommand{\resheading}[1]{
      \vspace{12pt}
      {\Large \color{primary}\textbf{#1}}
      \vspace{-4pt}
      \begin{center}\color{accent}\rule{\textwidth}{0.5pt}\end{center}
      \vspace{-8pt}
    }
    
    % Modern Subheading (Title, Location, Role, Date)
    \newcommand{\ressubheading}[4]{
      \vspace{4pt}
      \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
        \textbf{\color{primary}#1} & \color{text}#2 \\
        \textit{\color{text}#3} & \textit{\color{text}#4} \\
      \end{tabular*}\vspace{-4pt}
    }
    %-----------------------------------------------------------

    \begin{document}
    \color{text} % Set default text color
    """

workTitle = {
    "en": "Work experience",
    "da": "Arbejdserfaring",
    "de": "Berufserfahrung",
    "fr": "Expérience de travail",
    "it": "Esperienza di lavoro",
}

educationTitle = {
    "en": "Education",
    "da": "Uddannelse",
    "de": "Ausbildung",
    "fr": "L'éducation",
    "it": "Educazione",
}

languageTitle = {
    "en": "Language Skills",
    "da": "Sprogkundskaber",
    "de": "Sprachkenntnisse",
    "fr": "Compétences linguistiques",
    "it": "Competenze linguistiche",
}

skillTitle = {
    "en": "Technical Skills",
    "da": "Tekniske færdigheder",
    "de": "Andere Fähigkeiten",
    "fr": "Autres compétences",
    "it": "Altre competenze",
}

publicationTitle = {
    "en": "Publications",
    "da": "Publikationer",
    "de": "Publikationen",
    "fr": "Publications",
    "it": "Pubblicazioni",
}

def format_date(date_str: str, as_year_only=False):
    if not date_str or date_str.lower() == "present":
        return "Now"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y") if as_year_only else dt.strftime("%b %Y")
    except ValueError:
        return date_str

def generateMainDesign2(profile, language="en"):
    main = headerCV

    # Personal Information
    name = profile.get("name", "")
    if name:
        first_name = name.split(" ")[0]
        last_name = " ".join(name.split(" ")[1:])

        addr = profile.get("address") or {}
        city = addr.get("city", "")
        country = addr.get("country", "")
        
        contact = profile.get("contact") or {}
        phone = contact.get("phone", "")

        main += f"""
      \\begin{{tabular*}}{{\\textwidth}}{{l@{{\\extracolsep{{\\fill}}}}r}}
      \\textbf{{\\huge \\color{{primary}} {first_name} {last_name}}} & \\color{{text}} {phone} \\\\
      \\color{{text}} {city}, {country} & \\\\"""

        for website in profile.get("websites", []):
            w_type = website.get("website_type", "").lower()
            url = website.get("url", "")
            if "linkedin" in w_type:
                main += f"\n      \\color{{accent}}\\faLinkedin {{ }}  \\href{{{url}}}{{\\color{{text}}{url}}} & \\\\"
            elif "github" in w_type:
                main += f"\n      \\color{{accent}}\\faGithub {{ }}  \\href{{{url}}}{{\\color{{text}}{url}}} & \\\\"
            else:
                main += f"\n      \\color{{accent}}\\faGlobe {{ }}  \\href{{{url}}}{{\\color{{text}}{url}}} & \\\\"

        main += "\n      \\end{tabular*}\n      \\vspace{8pt}\n"

    # Professional Summary
    summary = profile.get("summary", "")
    if summary:
        main += f"\n\\resheading{{Professional Summary}}\n\\begin{{itemize}}\n\\item[] \\color{{text}} {summary}\n\\end{{itemize}}"

    # Work History
    jobs = profile.get("jobs", [])
    if jobs:
        main += f"\n\\resheading{{{workTitle.get(language, 'Work experience')}}}\n\\begin{{itemize}}"
        for job in jobs:
            start = format_date(job.get("start"))
            end = format_date(job.get("end"))
            city_country = f"{city}, {country}" if city else ""

            main += f"""\n        \\item[] \\ressubheading{{{job.get("company")}}}{{{city_country}}}{{{job.get("title")}}}{{{start} - {end}}}"""
            
            highlights = job.get("highlights", [])
            if highlights:
                main += "\n        \\begin{itemize}"
                for hl in highlights:
                    main += f"\n            \\resitem{{{hl}}}"
                main += "\n        \\end{itemize}"
        main += "\n      \\end{itemize}"

    # Projects
    projects = profile.get("projects", [])
    if projects:
        main += f"\n\\resheading{{Projects}}\n\\begin{{itemize}}"
        for proj in projects:
            start = format_date(proj.get("start"), True)
            end = format_date(proj.get("end"), True)
            date_str = f"{start} - {end}" if start != "Now" and end != "Now" else start
            
            main += f"""\n        \\item[] \\ressubheading{{{proj.get("name")}}}{{}}{{{proj.get("role")}}}{{{date_str}}}"""
            
            highlights = proj.get("highlights", [])
            if highlights:
                main += "\n        \\begin{itemize}"
                for hl in highlights:
                    main += f"\n            \\resitem{{{hl}}}"
                main += "\n        \\end{itemize}"
        main += "\n      \\end{itemize}"

    # Education
    education = profile.get("education", [])
    if education:
        main += f"\n\\resheading{{{educationTitle.get(language, 'Education')}}}\n\\begin{{itemize}}"
        for edu in education:
            start = format_date(edu.get("start_date"), True)
            end = format_date(edu.get("end_date"), True)
            city_country = f"{city}, {country}" if city else ""

            main += f"""\n\t\t    \\item[] \\ressubheading{{{edu.get("institution")}}}{{{city_country}}}{{{edu.get("degree")}}}{{{start} - {end}}}"""
        main += "\n      \\end{itemize}"

    # Courses & Certifications
    courses = profile.get("courses", [])
    if courses:
        main += f"\n\\resheading{{Courses \\& Certifications}}\n\\begin{{itemize}}"
        for crs in courses:
            date = format_date(crs.get("date"), True)
            main += f"""\n\t\t    \\item[] \\ressubheading{{{crs.get("title")}}}{{{crs.get("organized_by")}}}{{}}{{{date}}}"""
        main += "\n      \\end{itemize}"

    # Technical Skills / Languages
    skills = profile.get("skills", [])
    languages = profile.get("languages", [])
    if skills or languages:
        main += f"\n\\resheading{{{skillTitle.get(language, 'Skills')}}}\n\\begin{{itemize}}"

        if languages:
            langs = ", ".join(languages)
            main += f"\n\t\t    \\item[] \\textbf{{\\color{{primary}}{languageTitle.get(language, 'Language Skills')}}}: \\color{{text}}{langs}"

        if skills:
            skls = ", ".join(skills)
            main += f"\n\t\t    \\item[] \\textbf{{\\color{{primary}}Core Competencies}}: \\color{{text}}{skls}"

        main += "\n      \\end{itemize}"

    # Patents
    patents = profile.get("patents", [])
    if patents:
        main += f"\n\\resheading{{Patents}}\n\\begin{{itemize}}"
        for pat in patents:
            main += f"""\n\t\t    \\item[] \\ressubheading{{{pat.get("title")}}}{{{pat.get("number")}}}{{{pat.get("status")}}}{{{pat.get("date")}}}"""
        main += "\n      \\end{itemize}"

    # Publications
    publications = profile.get("publications", [])
    if publications:
        main += f"\n\\resheading{{{publicationTitle.get(language, 'Publications')}}}\n\\begin{{itemize}}"
        for pub in publications:
            main += f"""\n\t\t    \\item[] \\ressubheading{{{pub.get("title")}}}{{}}{{}}{{{pub.get("date")}}}"""
        main += "\n      \\end{itemize}"

    main += "\n    \\end{document}"
    return main