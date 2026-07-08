from datetime import datetime

headerCV = r"""
\documentclass[10pt]{scrartcl}

% Modern Layout & Columns
\usepackage[hmargin=1.25cm,vmargin=1.25cm,twocolumn,columnsep=1.25cm]{geometry}
\usepackage{tabularx,xcolor,needspace,enumitem,etoolbox} % <-- Added etoolbox back!
\usepackage[utf8]{inputenc}
\usepackage{fontawesome}

% Modern Fonts
\usepackage[sfdefault,light]{FiraSans}
\usepackage[T1]{fontenc}

\setcounter{secnumdepth}{-1}
\pagestyle{empty}
\setlength\parindent{0pt}

% Modern Color Palette
\definecolor{primary}{HTML}{1E293B} % Slate 800 (Text)
\definecolor{accent}{HTML}{0EA5E9}  % Sky 500 (Links & Headers)
\definecolor{boxbg}{HTML}{F1F5F9}   % Slate 100 (Contact Box Background)
\definecolor{textgray}{HTML}{475569} % Slate 600 (Subtitles)

\usepackage{hyperref}
\hypersetup{colorlinks,breaklinks,urlcolor=accent,linkcolor=accent}

\setkomafont{disposition}{\color{primary}}
\setkomafont{section}{\scshape\Large\mdseries\color{accent}}

% --- Custom Header ---
\renewcommand\part[1]{%
    \twocolumn[%
    \begin{center}
    \vskip-\lastskip%
    {\Huge\color{primary}\textbf{#1}} \medskip\\
    {\Large\color{textgray} Curriculum Vitae}
    \bigskip
    \end{center}]}

% --- Section Underline ---
\makeatletter
\let\old@section\section
\renewcommand\section[2][]{%
    \old@section[#1]{#2}%
    \newdimen\raising%
    \raising=\dimexpr-0.7\baselineskip\relax%
    \vskip\raising\hrule height 0.5pt\vskip-\raising}
\makeatother

% --- List Formatting ---
\setlist[itemize]{leftmargin=*, itemsep=1pt, topsep=2pt, parsep=0pt}
\setlist[itemize,1]{label=\color{accent}\faAngleRight, leftmargin=1em}

% --- Custom CV Event Commands ---
\newcommand{\cvevent}[4]{
    {\large\color{primary}\textbf{#2}} \\
    {\color{textgray}\textit{#3}} \hfill {\small\textsc{\color{accent}#1}} \vspace{2pt}\\
    {\small\color{primary}#4}
    \bigskip
}

\newenvironment{factlist}{%
    \newdimen\unbaseline
    \unbaseline=\dimexpr-\baselinestretch\baselineskip\relax
    \renewcommand\item[2]{%
    \textbf{\color{primary}##1} & {\raggedright\color{primary}##2\medskip\\}\\[\unbaseline]}
    \tabularx{\linewidth}{rX}}
    {\endtabularx\bigskip}

\begin{document}
\color{primary}
"""

def format_date(date_str: str, as_year_only=False):
    if not date_str or str(date_str).lower() == "present":
        return "Now"
    try:
        dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        return dt.strftime("%Y") if as_year_only else dt.strftime("%b %Y")
    except ValueError:
        return str(date_str)

def generateMainDesign4(profile, language="en"):
    main = headerCV

    # 1. Header (Name)
    name = profile.get("name", "Name Missing")
    main += f"\n\\part{{{name}}}\n"

    # 2. Contact Information Box (Dynamically built in Python to avoid empty fields)
    addr = profile.get("address", {})
    city = addr.get("city", "")
    country = addr.get("country", "")
    city_country = f"{city}, {country}" if city and country else city or country

    contact = profile.get("contact", {})
    phone = contact.get("phone", "")
    email = contact.get("email", "")

    websites = profile.get("websites", [])
    website_url = ""
    if websites and websites[0].get("url"):
        website_url = websites[0]["url"].replace("http://", "").replace("https://", "")

    main += r"""
\needspace{0.1\textheight}
\newdimen\boxwidth
\boxwidth=\dimexpr\linewidth-2\fboxsep\relax
\colorbox{boxbg}{
\begin{tabularx}{\boxwidth}{c|X}
"""
    if city_country:
        main += f"\\faMapMarker & \\color{{primary}}{city_country}\\smallskip\\\\\n"
    if phone:
        main += f"\\faPhone & \\color{{primary}}{phone}\\smallskip\\\\\n"
    if email:
        main += f"\\faEnvelope & \\href{{mailto:{email}}}{{{email}}}\\smallskip\\\\\n"
    if website_url:
        main += f"\\faGlobe & \\href{{https://{website_url}}}{{{website_url}}}\n"
        
    main += "\\end{tabularx}}\\bigskip\n"

    # 3. Summary
    summary = profile.get("summary", "")
    if summary:
        main += f"\\section{{Professional Summary}}\n{summary}\n\\bigskip\n"

    # 4. Work Experience
    jobs = profile.get("jobs", [])
    if jobs:
        main += f"\\section{{Work Experience}}\n"
        for job in jobs:
            start = format_date(job.get("start"))
            end = format_date(job.get("end"))
            date_str = f"{start} -- {end}"
            
            highlights = job.get("highlights", [])
            highlight_tex = ""
            if highlights:
                highlight_tex = "\\begin{itemize}\n"
                for hl in highlights:
                    highlight_tex += f"\\item {hl}\n"
                highlight_tex += "\\end{itemize}"

            main += f"\\cvevent{{{date_str}}}{{{job.get('title')}}}{{{job.get('company')}}}{{{highlight_tex}}}\n"

    # 5. Projects
    projects = profile.get("projects", [])
    if projects:
        main += f"\\section{{Projects}}\n"
        for proj in projects:
            start = format_date(proj.get("start"), True)
            end = format_date(proj.get("end"), True)
            date_str = f"{start} -- {end}" if start != "Now" and end != "Now" else start
            
            highlights = proj.get("highlights", [])
            highlight_tex = ""
            if highlights:
                highlight_tex = "\\begin{itemize}\n"
                for hl in highlights:
                    highlight_tex += f"\\item {hl}\n"
                highlight_tex += "\\end{itemize}"

            main += f"\\cvevent{{{date_str}}}{{{proj.get('name')}}}{{{proj.get('role')}}}{{{highlight_tex}}}\n"

    # 6. Education
    education = profile.get("education", [])
    if education:
        main += f"\\section{{Education}}\n"
        for edu in education:
            start = format_date(edu.get("start_date"), True)
            end = format_date(edu.get("end_date"), True)
            date_str = f"{start} -- {end}"
            
            desc = edu.get("description", "")
            
            main += f"\\cvevent{{{date_str}}}{{{edu.get('degree')}}}{{{edu.get('institution')}}}{{{desc}}}\n"

    # 7. Skills & Languages
    skills = profile.get("skills", [])
    languages = profile.get("languages", [])
    if skills or languages:
        main += f"\\section{{Skills \\& Languages}}\n\\begin{{factlist}}\n"
        if skills:
            skills_str = ", ".join(skills)
            main += f"\\item{{Core}}{{{skills_str}}}\n"
        if languages:
            langs_str = ", ".join(languages)
            main += f"\\item{{Languages}}{{{langs_str}}}\n"
        main += "\\end{factlist}\n"

    # 8. Patents & Publications
    patents = profile.get("patents", [])
    if patents:
        main += f"\\section{{Patents}}\n\\begin{{itemize}}\n"
        for pat in patents:
            main += f"\\item \\textbf{{{pat.get('title')}}} ({pat.get('date')}) - {pat.get('status')}\n"
        main += "\\end{itemize}\n\\bigskip\n"

    publications = profile.get("publications", [])
    if publications:
        main += f"\\section{{Publications}}\n\\begin{{itemize}}\n"
        for pub in publications:
            main += f"\\item \\textbf{{{pub.get('title')}}} ({pub.get('date')})\n"
        main += "\\end{itemize}\n"

    main += "\n\\end{document}"
    return main