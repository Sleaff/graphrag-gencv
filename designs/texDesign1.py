from datetime import datetime

headerCV = r"""
    \documentclass[letterpaper,11pt]{article}
    \newlength{\outerbordwidth}
    \pagestyle{empty}
    \raggedbottom
    \raggedright
    \usepackage[svgnames]{xcolor}
    \usepackage{framed}
    \usepackage{tocloft}

    \usepackage[T1]{fontenc}
    \usepackage{lmodern}
    \usepackage[utf8]{inputenc}
    \usepackage[]{babel}
    \usepackage{fontawesome}
    \usepackage{hyperref}

    %-----------------------------------------------------------
    %Edit these values as you see fit

    \setlength{\outerbordwidth}{2pt}  % Width of border outside of title bars
    \definecolor{shadecolor}{gray}{0.75}  % Outer background color of title bars (0 = black, 1 = white)
    \definecolor{shadecolorB}{gray}{0.93}  % Inner background color of title bars

    %-----------------------------------------------------------
    %Margin setup

    \setlength{\evensidemargin}{-0.25in}
    \setlength{\headheight}{0in}
    \setlength{\headsep}{0in}
    \setlength{\oddsidemargin}{-0.25in}
    \setlength{\paperheight}{11in}
    \setlength{\paperwidth}{8.5in}
    \setlength{\tabcolsep}{0in}
    \setlength{\textheight}{9.5in}
    \setlength{\textwidth}{7in}
    \setlength{\topmargin}{-0.3in}
    \setlength{\topskip}{0in}
    \setlength{\voffset}{0.1in}

    %-----------------------------------------------------------
    %Custom commands
    \newcommand{\resitem}[1]{\item #1 \vspace{-2pt}}
    \newcommand{\resheading}[1]{\vspace{6pt}
    \parbox{\textwidth}{\setlength{\FrameSep}{\outerbordwidth}
        \begin{shaded}
    \setlength{\fboxsep}{0pt}\framebox[\textwidth][l]{\setlength{\fboxsep}{2pt}\fcolorbox{shadecolorB}{shadecolorB}{\textbf{\sffamily{\mbox{~}\makebox[6.8in][l]{\large #1} \vphantom{p\^{E}}}}}}
        \end{shaded}
    }\vspace{-6pt}
    }
    \newcommand{\ressubheading}[4]{
    \begin{tabular*}{6.5in}{p{4.8in}@{\extracolsep{\fill}}r}
            \textbf{#1} & #2 \\
            \textit{#3} & \textit{#4} \\
    \end{tabular*}\vspace{-8pt}}
    %-----------------------------------------------------------

    \begin{document}
    """

workTitle = {
    "en": "Work Experience",
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
    "en": "Languages",
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
    if not date_str or str(date_str).strip().upper() == "N/A" or str(date_str).strip().lower() == "none":
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y") if as_year_only else dt.strftime("%b %Y")
    except ValueError:
        return date_str

def generateMainDesign1(profile, language="en"):
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
        email = contact.get("email", "")

        main += f"""
      \\begin{{tabular*}}{{7in}}{{l@{{\\extracolsep{{\\fill}}}}r}}
      \\textbf{{\\Large {first_name} {last_name}}} & {phone} \\\\
      {city}, {country} & {email} \\\\"""

        for website in profile.get("websites", []):
            w_type = website.get("website_type", "").lower()
            url = website.get("url", "")
            if "linkedin" in w_type:
                main += f"\n      \\faLinkedin {{ }}  \\href{{{url}}}{{{url}}} & \\\\"
            elif "github" in w_type:
                main += f"\n      \\faGithub {{ }}  \\href{{{url}}}{{{url}}} & \\\\"
            else:
                main += f"\n      \\faGlobe {{ }}  \\href{{{url}}}{{{url}}} & \\\\"

        main += "\n      \\end{tabular*}\n      \\vspace{5pt}\n"

    # Professional Summary
    summary = profile.get("summary", "")
    if summary:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\resheading{{Summary}}\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\begin{{itemize}}\n      \\item[] {summary}\n      \\end{{itemize}}"

    # Work History
    jobs = profile.get("jobs", [])
    if jobs:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\resheading{{{workTitle.get(language, 'Work Experience')}}}\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\begin{{itemize}}"
        for job in jobs:
            start = format_date(job.get("start"))
            end = format_date(job.get("end"))
            date_str = " - ".join(filter(None, [start, end]))
            job_addr = job.get("address") or {}
            job_city = job_addr.get("city", "")
            job_country = job_addr.get("country", "")
            
            if job_city and job_country:
                city_country = f"{job_city}, {job_country}"
            else:
                city_country = job_city or job_country or ""

            main += f"""\n        \\item \\ressubheading{{{job.get("company")}}}{{{city_country}}}{{{job.get("title")}}}{{{date_str}}}"""
            
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
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\resheading{{Projects}}\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\begin{{itemize}}"
        for proj in projects:
            start = format_date(proj.get("start"), True)
            end = format_date(proj.get("end"), True)
            date_str = " - ".join(filter(None, [start, end]))
            
            main += f"""\n        \\item \\ressubheading{{{proj.get("name")}}}{{}}{{{proj.get("role")}}}{{{date_str}}}"""
            
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
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{{educationTitle.get(language, 'Education')}}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        for edu in education:
            start = format_date(edu.get("start_date"), True)
            end = format_date(edu.get("end_date"), True)
            date_str = " - ".join(filter(None, [start, end]))

            main += f"""\n\t\t    \\item \\ressubheading{{{edu.get("institution")}}}{{{""}}}{{{edu.get("degree")}}}{{{date_str}}}"""
        main += "\n      \\end{itemize}"

    # Courses & Certifications
    courses = profile.get("courses", [])
    if courses:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{Courses \\& Certifications}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        for crs in courses:
            date = format_date(crs.get("date"), True)
            main += f"""\n\t\t    \\item \\ressubheading{{{crs.get("title")}}}{{{crs.get("organized_by")}}}{{}}{{{date}}}"""
        main += "\n      \\end{itemize}"

    # Technical Skills
    skills = profile.get("skills", [])
    if skills:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{{skillTitle.get(language, 'Skills')}}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        skls = ", ".join(skills)
        main += f"\n\t\t    \\item[] {skls}"
        main += "\n      \\end{itemize}"

    # Languages
    languages = profile.get("languages", [])
    if languages:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{{languageTitle.get(language, 'Languages')}}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        for lang in languages:
            if isinstance(lang, dict):
                lang_name = lang.get("name", "")
                proficiency = lang.get("proficiency", "")
                if lang_name and proficiency:
                    main += f"\n\t\t    \\item[] \\textbf{{{lang_name}}}: {proficiency}"
                elif lang_name:
                    main += f"\n\t\t    \\item[] {lang_name}"
            else:
                main += f"\n\t\t    \\item[] {lang}"
        main += "\n      \\end{itemize}"

    # Patents
    patents = profile.get("patents", [])
    if patents:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{Patents}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        for pat in patents:
            date = format_date(pat.get("date"))
            main += f"""\n\t\t    \\item \\ressubheading{{{pat.get("title")}}}{{{pat.get("number")}}}{{{pat.get("status")}}}{{{date}}}"""
        main += "\n      \\end{itemize}"

    # Publications
    publications = profile.get("publications", [])
    if publications:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{{publicationTitle.get(language, 'Publications')}}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        for pub in publications:
            date = format_date(pub.get("date"))
            main += f"""\n\t\t    \\item \\ressubheading{{{pub.get("title")}}}{{}}{{}}{{{date}}}"""
        main += "\n      \\end{itemize}"

    main += "\n    \\end{document}"
    return main