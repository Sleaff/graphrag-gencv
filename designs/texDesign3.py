from datetime import datetime

headerCV = r"""
\documentclass[letterpaper,11pt]{article}[leftmargin=*]

\usepackage[empty]{fullpage}
\usepackage{enumitem}
\usepackage[pdfnewwindow=true]{hyperref}
\usepackage{fontawesome}
\usepackage[sfdefault,light]{FiraSans}
\usepackage[T1]{fontenc}
\usepackage{anyfontsize}
\usepackage{xcolor}
\usepackage[utf8]{inputenc}

%-------------------------------------------------- SETTINGS HERE --------------------------------------------------
"""

settingsPart = r"""
\def \headertype {\doublecol} % \singlecol or \doublecol

% Misc settings
\def \entryspacing {-0pt}

\def \bulletstyle {\faAngleRight}

% Define colours
\definecolor{primary}{HTML}{000000}
\definecolor{secondary}{HTML}{0D47A1}
\definecolor{accent}{HTML}{263238}
\definecolor{links}{HTML}{1565C0}

%------------------------------------------------------------------------------------------------------------------- 

% Defines to make listing easier
\def \linkedin {\linkedinicon \hspace{3pt}\href{\linkedinlink}{\linkedintext}}
\def \phone {\phoneicon \hspace{3pt}{ \phonetext}}
\def \email {\emailicon \hspace{3pt}\href{\emaillink}{\emailtext}}
\def \github {\githubicon \hspace{3pt}\href{\githublink}{\githubtext}}
\def \website {\websiteicon \hspace{3pt}\href{\websitelink}{\websitetext}}

% Adjust margins
\addtolength{\oddsidemargin}{-0.55in}
\addtolength{\evensidemargin}{-0.55in}
\addtolength{\textwidth}{1.1in}
\addtolength{\topmargin}{-0.6in}
\addtolength{\textheight}{1.1in}

% Define the link colours
\hypersetup{
    colorlinks=true,
    urlcolor=links,
}

% Set the margin alignment 
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

%-------------------------
% Custom commands

% Sections
\renewcommand{\section}[2]{\vspace{5pt}
  \colorbox{secondary}{\color{white}\raggedbottom\normalsize\textbf{{#1}{\hspace{7pt}#2}}}
}
% Entry start and end, for spacing
\newcommand{\resumeEntryStart}{\begin{itemize}[leftmargin=2.5mm]}
\newcommand{\resumeEntryEnd}{\end{itemize}\vspace{\entryspacing}}

% Itemized list for the bullet points under an entry, if necessary
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=4.5mm]}
\newcommand{\resumeItemListEnd}{\end{itemize}}

% Resume item
\renewcommand{\labelitemii}{\bulletstyle}
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

% Entry with title, subheading, date(s), and location
\newcommand{\resumeEntryTSDL}[4]{
  \vspace{-1pt}\item[]
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{\color{primary}#1} & {\firabook\color{accent}\small#2} \\
      \textit{\color{accent}\small#3} & \textit{\color{accent}\small#4} \\
    \end{tabular*}\vspace{-6pt}
}

% Entry with title and date(s)
\newcommand{\resumeEntryTD}[2]{
  \vspace{-1pt}\item[]
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{\color{primary}#1} & {\firabook\color{accent}\small#2} \\
    \end{tabular*}\vspace{-6pt}
}

% Entry for special (skills)
\newcommand{\resumeEntryS}[2]{
  \item[]\small{
    \textbf{\color{primary}#1 }{ #2 \vspace{-6pt}}
  }
}

% Double column header
\newcommand{\doublecol}[6]{
  \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
    {
      \begin{tabular}[c]{l}
        \fontsize{35}{45}\selectfont{\color{primary}{{\textbf{\fullname}}}} \\
        {\textit{\subtitle}} 
      \end{tabular}
    } & {
      \begin{tabular}[c]{l@{\hspace{1.5em}}l}
        {\small#4} & {\small#1} \\
        {\small#5} & {\small#2} \\
        {\small#6} & {\small#3}
      \end{tabular}
    }
  \end{tabular*}
}

\begin{document}
%---------------------------------------------------- HEADER ----------------------------------------------------

\headertype{\linkedin}{\github}{\website}{\phone}{\email}{} % Set the order of items here
\vspace{-10pt} 

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


def generateMainDesign3(profile, language="en"):
    main = headerCV

    # Write personal information about the user
    name = profile.get("name", "")
    main += f"\\def \\fullname {{{name}}}\n\\def \\subtitle {{}}\n"

    contact = profile.get("contact", {})
    phone = contact.get("phone", "")
    email = contact.get("email", "")

    if phone:
        main += f"\\def \\phoneicon {{\\faPhone}}\n\\def \\phonetext {{{phone}}}\n"
    else:
        main += "\\def \\phoneicon {}\n\\def \\phonetext {}\n"

    if email:
        main += f"\\def \\emailicon {{\\faEnvelope}}\n\\def \\emaillink {{mailto:{email}}} \\def \\emailtext {{{email}}}\n"
    else:
        main += "\\def \\emailicon {}\n\\def \\emaillink {} \\def \\emailtext {}\n"

    # Social/Websites loop
    linkedin_url = ""
    github_url = ""
    website_url = ""

    for website in profile.get("websites", []):
        w_type = website.get("website_type", "").lower()
        url = website.get("url", "")
        if "linkedin" in w_type:
            linkedin_url = url
        elif "github" in w_type:
            github_url = url
        else:
            website_url = url

    if linkedin_url:
        main += f"\\def \\linkedinicon {{\\faLinkedin}}\n\\def \\linkedinlink {{{linkedin_url}}} \\def \\linkedintext {{{linkedin_url}}}\n"
    else:
        main += "\\def \\linkedinicon {}\n\\def \\linkedinlink {} \\def \\linkedintext {}\n"

    if github_url:
        main += f"\\def \\githubicon {{\\faGithub}}\n\\def \\githublink {{{github_url}}} \\def \\githubtext {{{github_url}}}\n"
    else:
        main += "\\def \\githubicon {}\n\\def \\githublink {} \\def \\githubtext {}\n"

    if website_url:
        main += f"\\def \\websiteicon {{\\faGlobe}}\n\\def \\websitelink {{{website_url}}} \\def \\websitetext {{{website_url}}}\n"
    else:
        main += "\\def \\websiteicon {}\n\\def \\websitelink {} \\def \\websitetext {}\n"

    main += settingsPart

    addr = profile.get("address") or {}
    city = addr.get("city", "")
    country = addr.get("country", "")
    city_country = f"{city}, {country}" if city and country else city or country

    # Professional Summary
    summary = profile.get("summary", "")
    if summary:
        main += f"\n%--- SUMMARY ---\n\\section{{\\faUser}}{{Professional Summary}}\n"
        main += f"\\vspace{{3pt}}\\small{{{summary}}}\\vspace{{5pt}}\n"

    # Work Experience
    jobs = profile.get("jobs", [])
    if jobs:
        main += f"\n%--- EXPERIENCE ---\n\\section{{\\faPieChart}}{{{workTitle.get(language, 'Work experience')}}}\n"
        for job in jobs:
            start = format_date(job.get("start"))
            end = format_date(job.get("end"))

            main += f"""  \\resumeEntryStart
        \\resumeEntryTSDL
        {{{job.get('company')}}}{{{start} -- {end}}}
        {{{job.get('title')}}}{{{city_country}}}"""
            
            highlights = job.get("highlights", [])
            if highlights:
                main += "\n        \\resumeItemListStart"
                for hl in highlights:
                    main += f"\n        \\resumeItem {{{hl}}}"
                main += "\n        \\resumeItemListEnd"
            main += "\n        \\resumeEntryEnd\n"

    # Projects
    projects = profile.get("projects", [])
    if projects:
        main += f"\n%--- PROJECTS ---\n\\section{{\\faFlask}}{{Projects}}\n"
        for proj in projects:
            start = format_date(proj.get("start"), True)
            end = format_date(proj.get("end"), True)
            date_str = f"{start} -- {end}" if start != "Now" and end != "Now" else start

            main += f"""  \\resumeEntryStart
        \\resumeEntryTSDL
        {{{proj.get('name')}}}{{{date_str}}}
        {{{proj.get('role')}}}{{}}"""
            
            highlights = proj.get("highlights", [])
            if highlights:
                main += "\n        \\resumeItemListStart"
                for hl in highlights:
                    main += f"\n        \\resumeItem {{{hl}}}"
                main += "\n        \\resumeItemListEnd"
            main += "\n        \\resumeEntryEnd\n"

    # Education
    education = profile.get("education", [])
    if education:
        main += f"\n%--- EDUCATION ---\n\\section{{\\faGraduationCap}}{{{educationTitle.get(language, 'Education')}}}\n"
        for edu in education:
            start = format_date(edu.get("start_date"), True)
            end = format_date(edu.get("end_date"), True)

            main += f"""  \\resumeEntryStart
        \\resumeEntryTSDL
        {{{edu.get('institution')}}}{{{start} -- {end}}}
        {{{edu.get('degree')}}}{{{city_country}}}
        \\resumeEntryEnd
        """

    # Skills & Languages
    skills = profile.get("skills", [])
    languages = profile.get("languages", [])
    if skills or languages:
        main += f"\n%--- SKILLS ---\n\\section{{\\faGears}}{{{skillTitle.get(language, 'Technical Skills')}}} \\resumeEntryStart\n"

        if languages:
            langs = ", ".join(languages)
            main += f"  \\resumeEntryS{{{languageTitle.get(language, 'Language Skills')}: }}{{{langs}}}\n"

        if skills:
            skls = ", ".join(skills)
            main += f"  \\resumeEntryS{{Core Competencies: }}{{{skls}}}\n"

        main += "  \\resumeEntryEnd\n"

    main += "\n\\end{document}"
    return main