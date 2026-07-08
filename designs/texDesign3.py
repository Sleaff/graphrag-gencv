from datetime import datetime

headerCV3 = r"""
\documentclass[10pt]{scrartcl}

\usepackage[hmargin=1.25cm,vmargin=1.25cm,twocolumn,columnsep=1.25cm]{geometry}
\usepackage{bookman,etoolbox,hyperref,marvosym,needspace,tabularx,xcolor}
\usepackage[utf8]{inputenc}
\usepackage{fontawesome}

\setcounter{secnumdepth}{-1}

\newcommand\ucwords[2][3]{%
    \providecommand\directlua[1]{#2}%
    \directlua{%
    local minlen=tonumber("#1")
    local src="\luaescapestring{\unexpanded{#2}}"
    local dst={}
    for w in src:gmatch('[^\string\%s]+') do
        if w:len() >= minlen then w = w:sub(1,1):upper()..w:sub(2) end
        table.insert(dst, w)
    end
    tex.print(dst)}}

\pagestyle{empty}
\setlength\parindent{0pt}
\color[HTML]{303030}
\definecolor{link}{HTML}{506060}
\hypersetup{colorlinks,breaklinks,urlcolor=link,linkcolor=link}
\setkomafont{disposition}{\color[HTML]{801010}}
\setkomafont{section}{\scshape\Large\mdseries}

\renewcommand\part[1]{%
    \twocolumn[%
    \begin{center}
    \vskip-\lastskip%
    {\usekomafont{part} #1} \medskip\\
    {\fontfamily{pzc}\selectfont\Huge Curriculum vitae}
    \bigskip
    \end{center}]}

\makeatletter
\let\old@section\section
\renewcommand\section[2][]{%
    \old@section[#1]{\ucwords{#2}}%
    \newdimen\raising%
    \raising=\dimexpr-0.7\baselineskip\relax%
    \vskip\raising\hrule height 0.4pt\vskip-\raising}
\makeatother

\newcommand\ifjob[3]{%
    \edef\JOBNAME{\jobname}%
    \edef\PIVOT{\detokenize{#1}}%
    \ifdefstrequal{\JOBNAME}{\PIVOT}{#2}{#3}%
}

\newcommand\personal[4][]{%
    \needspace{0.5\textheight}%
    \newdimen\boxwidth%
    \boxwidth=\dimexpr\linewidth-2\fboxsep\relax%
    \colorbox[HTML]{F5DD9D}{%
    \begin{tabularx}{\boxwidth}{c|X}
    \Writinghand & {#2}\smallskip\\
    \Telefon     & {#3}\smallskip\\
    \Letter      & \href{mailto:#4}{#4}
    \ifstrempty{#1}{}{\smallskip\\ \Lightning & \href{http://#1}{#1}}
    \end{tabularx}}}

\newenvironment{eventlist}{%
    \newcommand*\inskip{}
    \renewcommand\item[3]{%
    \inskip%
    {\raggedleft\textsc{##1}\\[1pt]}
    {##2}\\[2pt]
    {\Large\textit{##3}}
    \medskip
    \renewcommand\inskip{\bigskip}}}
    {\bigskip}

\newenvironment{yearlist}{%
    \renewcommand\item[4][]{%
    {\textsc{##2}} & {\bfseries ##3} \\
    \ifstrempty{##1}{}{& {\textsc{##1}} \\}
    & {\textit{##4}}\medskip\\}
    \tabularx{\linewidth}{rX}}
    {\endtabularx}

\newenvironment{factlist}{%
    \newdimen\unbaseline
    \unbaseline=\dimexpr-\baselinestretch\baselineskip\relax
    \renewcommand\item[2]{%
    \textsc{##1} & {\raggedright ##2\medskip\\}\\[\unbaseline]}
    \tabularx{\linewidth}{rX}}
    {\endtabularx}

\newenvironment{otherlist}{%
    \newcommand*\inskip{}
    \renewcommand\item[2]{%
    \inskip%
    {##2}\\[2pt]
    \renewcommand\inskip{\bigskip}}}
    {\bigskip}

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

honorsTitle = {
    "en": "Honors & Awards",
    "da": "Priser og anerkendelser",
    "de": "Auszeichnungen",
    "fr": "Prix et distinctions",
    "it": "Premi e riconoscimenti",
}


def format_date(date_str: str, as_year_only=False):
    if not date_str or str(date_str).lower() == "present":
        return "Now"
    try:
        dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        return dt.strftime("%Y") if as_year_only else dt.strftime("%b %Y")
    except ValueError:
        return str(date_str)


def generateMainDesign3(profile, language="en"):
    main = headerCV3

    safe_name = getattr(profile, "name", "") or "Name Missing"
    names = safe_name.split(" ", 1)
    first_name = names[0]
    last_name = names[1] if len(names) > 1 else ""
    main += f"\n\\part{{{first_name} {last_name}}}\n"

    address = getattr(profile, "address", None)
    city = getattr(address, "city", "") if address else ""
    country = getattr(address, "country", "") if address else ""
    city_country = f"{city} ({country})" if city and country else city or country

    experiences = getattr(profile, "experiences", [])
    if experiences:
        main += f"\n\\section{{{workTitle.get(language, 'Work experience')}}}\n\\begin{{eventlist}}\n"
        for exp in experiences:
            start = format_date(getattr(exp, "start_date", ""))
            end = format_date(getattr(exp, "end_date", ""))
            company = getattr(exp, "company_name", "")
            job_title = getattr(exp, "job_title", "")
            desc = getattr(exp, "description", "")

            loc = f"{company}, {city}" if city else company
            main += f"""
        \\item{{{start} - {end}}}
        {{{loc}}}
        {{{job_title}}}
        {desc}
        """
        main += "\\end{eventlist}\n"

    websites = getattr(profile, "websites", [])
    website_url = ""
    if websites and getattr(websites[0], "url", ""):
        website_url = websites[0].url.replace("http://", "").replace("https://", "")

    phone = getattr(profile, "phone_number", "") or ""
    email = getattr(profile, "email", "") or ""

    main += f"""
      \\personal
        [{website_url}]
        {{{city_country}}}
        {{{phone}}}
        {{{email}}}
      """

    education = getattr(profile, "education", [])
    if education:
        main += f"\n\\section{{{educationTitle.get(language, 'Education')}}}\n\\begin{{yearlist}}\n"
        for edu in education:
            start = format_date(getattr(edu, "start_date", ""), True)
            end = format_date(getattr(edu, "end_date", ""), True)
            degree = getattr(edu, "degree", "")
            field = getattr(edu, "field_of_study", "")
            inst = getattr(edu, "institution", "")

            loc = f"{inst}, {city}" if city else inst
            main += f"""
        \\item[{degree}]{{{start} -- {end}}}
        {{{field}}}
        {{{loc}}}
        """
        main += "\\end{yearlist}\n"

    languages = getattr(profile, "languages", [])
    if languages:
        main += f"\n\\section{{{languageTitle.get(language, 'Language Skills')}}}\n\\begin{{factlist}}\n"
        for lang in languages:
            name = getattr(lang, "name", "")
            prof = getattr(lang, "proficiency", "")
            main += f"\\item{{{name}}}{{{prof}}}\n"
        main += "\\end{factlist}\n"

    technical_skills = getattr(profile, "technical_skills", [])
    if technical_skills:
        main += f"\n\\section{{{skillTitle.get(language, 'Technical Skills')}}}\n\\begin{{factlist}}\n"
        skill_list = [
            s if isinstance(s, str) else getattr(s, "name", "")
            for s in technical_skills
        ]
        skills_str = ", ".join(filter(bool, skill_list))
        main += f"\\item{{Skills}}{{{skills_str}}}\n"
        main += "\\end{factlist}\n"

    publications = getattr(profile, "publications", [])
    if publications:
        main += f"\n\\section{{{publicationTitle.get(language, 'Publications')}}}\n\\begin{{otherlist}}\n"
        for pub in publications:
            title = getattr(pub, "title", "")
            date = getattr(pub, "date", "")
            publisher = getattr(pub, "publisher", "")
            desc = getattr(pub, "description", "")
            main += f"\\item{{{title} ({date})}}{{{publisher}: {desc}}}\n"
        main += "\\end{otherlist}\n"

    honors = getattr(profile, "honors", [])
    if honors:
        main += f"\n\\section{{{honorsTitle.get(language, 'Honors & Awards')}}}\n\\begin{{otherlist}}\n"
        for honor in honors:
            title = getattr(honor, "title", "")
            date = getattr(honor, "date", "")
            issuer = getattr(honor, "issuer", "")
            main += f"\\item{{{title} ({date})}}{{{issuer}}}\n"
        main += "\\end{otherlist}\n"

    main += "\n\\end{document}"
    return main


def generateMainDesign3Enriched(profile, language="en"):
    return generateMainDesign3(profile, language)
