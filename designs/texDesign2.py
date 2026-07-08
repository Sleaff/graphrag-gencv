from datetime import datetime

headerCV2 = r"""
\documentclass[letterpaper,12pt]{article}[leftmargin=*]

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

settingsPart2 = r"""
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


def generateMainDesign2(profile, language="en"):
    main = headerCV2

    # Write personal information about the user[cite: 5]
    if profile.name:
        main += f"\\def \\fullname {{{profile.name}}}\n\\def \\subtitle {{}}\n"

    # Default missing properties to empty strings if not present in your schema
    phone = getattr(profile, "phone_number", "")
    email = getattr(profile, "email", "")

    if phone:
        main += f"\\def \\phoneicon {{\\faPhone}}\n\\def \\phonetext {{{phone}}}\n"
    else:
        main += "\\def \\phoneicon {}\n\\def \\phonetext {}\n"

    if email:
        main += f"\\def \\emailicon {{\\faEnvelope}}\n\\def \\emaillink {{mailto:{email}}} \\def \\emailtext {{{email}}}\n"
    else:
        main += "\\def \\emailicon {}\n\\def \\emaillink {} \\def \\emailtext {}\n"

    # Empty fallbacks for layout macros
    main += "\\def \\linkedinicon {}\n\\def \\linkedinlink {} \\def \\linkedintext {}\n"
    main += "\\def \\githubicon {}\n\\def \\githublink {} \\def \\githubtext {}\n"
    main += "\\def \\websiteicon {}\n\\def \\websitelink {} \\def \\websitetext {}\n"

    main += settingsPart2

    # Write website information about the user below header[cite: 5]
    if profile.websites:
        for website in profile.websites:
            if "linkedin" in website.website_type.lower():
                main += f"\\faLinkedin {{ }}  \\href{{{website.url}}}{{{website.url}}} \\newline\n"
            elif "xing" in website.website_type.lower():
                main += f"\\faXing {{ }}  \\href{{{website.url}}}{{{website.url}}} \\newline\n"
            else:
                main += f"\\faGlobe {{ }}  \\href{{{website.url}}}{{{website.url}}} \\newline\n"

    main += "\\newline\n"

    # Write educational information about the user[cite: 5]
    if profile.education:
        main += f"\n%--- EDUCATION ---\n\\section{{\\faGraduationCap}}{{{educationTitle.get(language, 'Education')}}}\n"
        for edu in profile.education:
            start = format_date(edu.start_date, True)
            end = format_date(edu.end_date, True)
            city_country = (
                f"{profile.address.city}, {profile.address.country}"
                if profile.address
                else ""
            )

            main += f"""  \\resumeEntryStart
        \\resumeEntryTSDL
        {{{edu.institution}}}{{{start} -- {end}}}
        {{{edu.degree} {edu.field_of_study}}}{{{city_country}}}
        \\resumeEntryEnd
        """

    # Write experience information about the user[cite: 5]
    if profile.experiences:
        main += f"\n%--- EXPERIENCE ---\n\\section{{\\faPieChart}}{{{workTitle.get(language, 'Work experience')}}}\n"
        for exp in profile.experiences:
            start = format_date(exp.start_date)
            end = format_date(exp.end_date)
            city_country = (
                f"{profile.address.city}, {profile.address.country}"
                if profile.address
                else ""
            )

            main += f"""  \\resumeEntryStart
        \\resumeEntryTSDL
        {{{exp.company_name}}}{{{start} -- {end}}}
        {{{exp.job_title}}}{{{city_country}}}
        \\resumeItemListStart
        \\resumeItem {{{exp.description}}}
        \\resumeItemListEnd
        \\resumeEntryEnd
        """

    # Write publication information about the user[cite: 5]
    if profile.publications:
        main += f"\n%--- PUBLICATIONS ---\n\\section{{\\faBook}}{{{publicationTitle.get(language, 'Publications')}}}\n"
        for pub in profile.publications:
            main += f"""  \\resumeEntryStart
        \\resumeEntryTSDL
        {{{pub.title}}}{{{pub.date}}}
        {{{pub.publisher}}}{{}}
        \\resumeItemListStart
        \\resumeItem {{{pub.description}}}
        \\resumeItemListEnd
        \\resumeEntryEnd
        """

    # Write skill information about the user[cite: 5]
    if profile.languages or profile.technical_skills:
        main += f"\n%--- SKILLS ---\n\\section{{\\faGears}}{{{skillTitle.get(language, 'Technical Skills')}}} \\resumeEntryStart\n"

        if profile.languages:
            langs = ", ".join([l.name for l in profile.languages])
            main += f"  \\resumeEntryS{{{languageTitle.get(language, 'Language Skills')} }}{{{langs}}}\n"

        if profile.technical_skills:
            skills = ", ".join(profile.technical_skills)
            main += f"  \\resumeEntryS{{{otherTitle.get(language, 'Other Skills')} }}{{{skills}}}\n"

        main += "  \\resumeEntryEnd\n"

    main += "\n\\end{document}"
    return main


def generateMainDesign2Enriched(profile, language="en"):
    # With direct Pydantic models, enriched queries are handled in the ingestion phase,
    # not the rendering phase. We can simply return the base generator.
    return generateMainDesign2(profile, language)
