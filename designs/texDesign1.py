from datetime import datetime

headerCV1 = r"""
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

    \setlength{\outerbordwidth}{3pt}  % Width of border outside of title bars
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
    \newcommand{\resheading}[1]{\vspace{8pt}
    \parbox{\textwidth}{\setlength{\FrameSep}{\outerbordwidth}
        \begin{shaded}
    \setlength{\fboxsep}{0pt}\framebox[\textwidth][l]{\setlength{\fboxsep}{4pt}\fcolorbox{shadecolorB}{shadecolorB}{\textbf{\sffamily{\mbox{~}\makebox[6.762in][l]{\large #1} \vphantom{p\^{E}}}}}}
        \end{shaded}
    }\vspace{-5pt}
    }
    \newcommand{\ressubheading}[4]{
    \begin{tabular*}{6.5in}{l@{\extracolsep{\fill}}r}
            \textbf{#1} & #2 \\
            \textit{#3} & \textit{#4} \\
    \end{tabular*}\vspace{-6pt}}
    %-----------------------------------------------------------

    \begin{document}
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

otherTitle = {
    "en": "Other Skills",
    "da": "Andre færdigheder",
    "de": "Sonstige Skills",
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


def generateMainDesign1(profile, language="en"):
    main = headerCV1

    # Personal Information[cite: 1]
    name = profile.get("name", "")
    if name:
        first_name = name.split(" ")[0]
        last_name = " ".join(name.split(" ")[1:])

        addr = profile.get("address") or {}
        city = addr.get("city", "")
        country = addr.get("country", "")

        main += f"""
      \\begin{{tabular*}}{{7in}}{{l@{{\\extracolsep{{\\fill}}}}r}}
      \\textbf{{\\Large {first_name} {last_name}}} & \\textbf{{\\today}} \\\\
      {city}, {country} & \\\\"""

        # Website loop[cite: 1]
        for website in profile.get("websites", []):
            w_type = website.get("website_type", "").lower()
            url = website.get("url", "")
            if "linkedin" in w_type:
                main += f"\n      \\faLinkedin {{ }}  \\href{{{url}}}{{{url}}} & \\\\"
            elif "xing" in w_type:
                main += f"\n      \\faXing {{ }}  \\href{{{url}}}{{{url}}} & \\\\"
            else:
                main += f"\n      \\faGlobe {{ }}  \\href{{{url}}}{{{url}}} & \\\\"

        main += "\n      \\end{tabular*}\n      \\\\"

    # Work History[cite: 1]
    jobs = profile.get("jobs", [])
    if jobs:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\resheading{{{workTitle.get(language, 'Work experience')}}}\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n      \\begin{{itemize}}"
        for job in jobs:
            start = format_date(job.get("start"))
            end = format_date(job.get("end"))
            city_country = f"{city}, {country}" if city else ""

            main += f"""
        \\item \\ressubheading{{{job.get("company")}}}{{{city_country}}}{{{job.get("title")}}}{{{start} - {end}}}\\\\"""

        main += "\n      \\end{itemize}"

    # Education[cite: 1]
    education = profile.get("education", [])
    if education:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{{educationTitle.get(language, 'Education')}}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        for edu in education:
            start = format_date(edu.get("start_date"), True)
            end = format_date(edu.get("end_date"), True)
            city_country = f"{city}, {country}" if city else ""

            main += f"""
		    \\item \\ressubheading{{{edu.get("institution")}}}{{{city_country}}}{{{edu.get("degree")}}}{{{start} - {end}}}\\\\"""

        main += "\n      \\end{itemize}"

    # Technical Skills / Languages[cite: 1]
    skills = profile.get("skills", [])
    languages = profile.get("languages", [])
    if skills or languages:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{{skillTitle.get(language, 'Skills')}}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"

        if languages:
            langs = ", ".join(languages)
            main += f"\n\t\t    \\item[] \\ressubheading{{{languageTitle.get(language, 'Language Skills')}}}{{}}{{}}{{}}\\\\*{langs}"

        if skills:
            skls = ", ".join(skills)
            main += f"\n\t\t    \\item[] \\ressubheading{{Core Competencies}}{{}}{{}}{{}}\\\\*{skls}"

        main += "\n      \\end{itemize}"

    # Publications[cite: 1]
    publications = profile.get("publications", [])
    if publications:
        main += f"\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{{{publicationTitle.get(language, 'Publications')}}}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{{itemize}}"
        for pub in publications:
            main += f"""
		    \\item \\ressubheading{{{pub.get("title")}}}{{}}{{}}{{{pub.get("date")}}}\\\\"""
        main += "\n      \\end{itemize}"

    # Honors/Awards[cite: 1]
    honors = profile.get("honors", [])
    if honors:
        main += "\n      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\resheading{Honors \\& Awards}\n\t    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\t    \\begin{itemize}"
        for honor in honors:
            main += f"""
		    \\item \\ressubheading{{{honor.get("title")}}}{{{honor.get("issuer")}}}{{}}{{{honor.get("date")}}}\\\\"""
        main += "\n      \\end{itemize}"

    main += "\n    \\end{document}"
    return main
