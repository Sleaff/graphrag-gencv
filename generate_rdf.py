import re

from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDFS, SKOS, XSD
from SPARQLWrapper import POST, SPARQLWrapper

from settings import GRAPHDB_URL

MY0 = Namespace("http://example.com/resume2rdf_ontology.rdf#")
MYVALUE0 = Namespace("http://example.com/resume2rdf_value_ontology.rdf#")
ESCO = Namespace("http://data.europa.eu/esco/model#")
COUNTRY = Namespace("http://www.bpiresearch.com/BPMO/2004/03/03/cdl/Countries#")
GRAPHDB_URL = GRAPHDB_URL + "/statements"


def sanitize_uri_string(text: str) -> str:
    if not text:
        return "unknown"
    return re.sub(r"[^a-z0-9_]", "", text.lower().strip().replace(" ", "_"))


def create_rdf_graph(candidate_data: dict) -> Graph:
    g = Graph()
    g.bind("my0", MY0)
    g.bind("myvalue0", MYVALUE0)
    g.bind("esco", ESCO)
    g.bind("country", COUNTRY)

    candidate_slug = sanitize_uri_string(candidate_data.get("name", "Unknown"))
    cv_uri = URIRef(f"http://example.com/data/cv_{candidate_slug}")
    person_uri = URIRef(f"http://example.com/data/person_{candidate_slug}")

    g.add((cv_uri, RDF.type, MY0.CV))
    g.add((cv_uri, MY0.aboutPerson, person_uri))
    g.add((person_uri, RDF.type, MY0.Person))
    g.add(
        (
            person_uri,
            MY0.firstName,
            Literal(candidate_data.get("name", ""), datatype=XSD.string),
        )
    )

    if candidate_data.get("gender"):
        gen_uri = URIRef(
            f"http://example.com/data/gender_{sanitize_uri_string(candidate_data['gender'])}"
        )
        g.add((person_uri, MY0.gender, gen_uri))
        g.add((gen_uri, RDF.type, MYVALUE0.GenderProperty))
        g.add(
            (
                gen_uri,
                RDFS.label,
                Literal(candidate_data["gender"], datatype=XSD.string),
            )
        )
    if candidate_data.get("nationality"):
        nat_uri = URIRef(
            f"http://www.bpiresearch.com/BPMO/2004/03/03/cdl/Countries#{sanitize_uri_string(candidate_data['nationality'])}"
        )
        g.add((person_uri, MY0.hasNationality, nat_uri))
        g.add((nat_uri, RDF.type, COUNTRY.ISO3166DefinedCountry))
    if candidate_data.get("date_of_birth"):
        g.add(
            (
                person_uri,
                MY0.dateOfBirth,
                Literal(candidate_data["date_of_birth"], datatype=XSD.string),
            )
        )
    if candidate_data.get("drivers_licence"):
        g.add(
            (
                person_uri,
                MY0.driversLicence,
                Literal(candidate_data["drivers_licence"], datatype=XSD.string),
            )
        )
    if candidate_data.get("short_description"):
        g.add(
            (
                person_uri,
                MY0.personShortDescription,
                Literal(candidate_data["short_description"], datatype=XSD.string),
            )
        )
    if candidate_data.get("long_description"):
        g.add(
            (
                person_uri,
                MY0.personLongDescription,
                Literal(candidate_data["long_description"], datatype=XSD.string),
            )
        )
    if candidate_data.get("email"):
        g.add(
            (
                person_uri,
                MY0.email,
                Literal(candidate_data["email"], datatype=XSD.string),
            )
        )
    if candidate_data.get("phone_mobile"):
        g.add(
            (
                person_uri,
                MY0.phoneNumberMobile,
                Literal(candidate_data["phone_mobile"], datatype=XSD.string),
            )
        )
    if candidate_data.get("phone_home"):
        g.add(
            (
                person_uri,
                MY0.phoneNumberHome,
                Literal(candidate_data["phone_home"], datatype=XSD.string),
            )
        )
    if candidate_data.get("phone_work"):
        g.add(
            (
                person_uri,
                MY0.phoneNumberWork,
                Literal(candidate_data["phone_work"], datatype=XSD.string),
            )
        )

    for idx, job in enumerate(candidate_data.get("jobs", [])):
        work_uri = URIRef(f"http://example.com/data/work_{candidate_slug}_{idx}")
        company_name = job.get("company", "Unknown")
        company_uri = URIRef(
            f"http://example.com/data/comp_{sanitize_uri_string(company_name)}"
        )

        g.add((cv_uri, MY0.hasWorkHistory, work_uri))
        g.add((work_uri, RDF.type, MY0.WorkHistory))
        g.add(
            (work_uri, MY0.jobTitle, Literal(job.get("title", ""), datatype=XSD.string))
        )
        g.add(
            (
                work_uri,
                MY0.startDate,
                Literal(job.get("start", ""), datatype=XSD.string),
            )
        )
        if job.get("end"):
            g.add(
                (
                    work_uri,
                    MY0.endDate,
                    Literal(job.get("end", ""), datatype=XSD.string),
                )
            )
        if job.get("description"):
            g.add(
                (
                    work_uri,
                    MY0.jobDescription,
                    Literal(job.get("description", ""), datatype=XSD.string),
                )
            )
        g.add(
            (
                work_uri,
                MY0.isCurrent,
                Literal(job.get("is_current", False), datatype=XSD.boolean),
            )
        )
        g.add((work_uri, MY0.employedIn, company_uri))
        g.add((company_uri, RDF.type, MY0.Company))
        g.add((company_uri, MY0.orgName, Literal(company_name, datatype=XSD.string)))

        for skill_dict in job.get("esco_skills", []):
            skill_name = skill_dict.get("name", "")
            esco_data = skill_dict.get("esco_data")

            if esco_data and esco_data.get("uri"):
                g.add((work_uri, MY0.hasSkill, URIRef(esco_data["uri"])))
                g.add(
                    (
                        URIRef(esco_data["uri"]),
                        MY0.skillName,
                        Literal(skill_name, datatype=XSD.string),
                    )
                )
            else:
                custom_skill_uri = URIRef(
                    f"http://example.com/data/custom_skill_{candidate_slug}_{sanitize_uri_string(skill_name)}"
                )
                g.add((work_uri, MY0.hasSkill, custom_skill_uri))
                g.add((custom_skill_uri, RDF.type, MY0.Skill))
                g.add(
                    (
                        custom_skill_uri,
                        MY0.skillName,
                        Literal(skill_name, datatype=XSD.string),
                    )
                )

        if job.get("career_level"):
            cl_str = job.get("career_level")
            cl_uri = URIRef(
                f"http://example.com/data/careerlevel_{sanitize_uri_string(cl_str)}"
            )
            g.add((work_uri, MY0.careerLevel, cl_uri))
            g.add((cl_uri, RDF.type, MYVALUE0.CVCareerLevel))
            g.add((cl_uri, RDFS.label, Literal(cl_str, datatype=XSD.string)))
        if job.get("job_type"):
            jt_str = job.get("job_type")
            jt_uri = URIRef(
                f"http://example.com/data/jobtype_{sanitize_uri_string(jt_str)}"
            )
            g.add((work_uri, MY0.jobType, jt_uri))
            g.add((jt_uri, RDF.type, MYVALUE0.CVEmploymentType))
            g.add((jt_uri, RDFS.label, Literal(jt_str, datatype=XSD.string)))
        if job.get("vector_id"):
            g.add(
                (
                    work_uri,
                    MY0.hasVectorReference,
                    Literal(job["vector_id"], datatype=XSD.string),
                )
            )

    for idx, edu in enumerate(candidate_data.get("education", [])):
        edu_uri = URIRef(f"http://example.com/data/edu_{candidate_slug}_{idx}")
        org_uri = URIRef(
            f"http://example.com/data/uni_{sanitize_uri_string(edu.get('institution', ''))}"
        )

        g.add((cv_uri, MY0.hasEducation, edu_uri))
        g.add((edu_uri, RDF.type, MY0.Education))
        g.add(
            (
                edu_uri,
                MY0.degreeFieldOfStudy,
                Literal(edu.get("field_of_study", ""), datatype=XSD.string),
            )
        )
        g.add(
            (
                edu_uri,
                MY0.eduStartDate,
                Literal(edu.get("start_date", ""), datatype=XSD.string),
            )
        )
        g.add(
            (
                edu_uri,
                MY0.eduGradDate,
                Literal(edu.get("end_date", ""), datatype=XSD.string),
            )
        )
        g.add((edu_uri, MY0.studiedIn, org_uri))
        g.add((org_uri, RDF.type, MY0.EducationalOrg))
        g.add(
            (
                org_uri,
                MY0.orgName,
                Literal(edu.get("institution", ""), datatype=XSD.string),
            )
        )
        if edu.get("description"):
            g.add(
                (
                    edu_uri,
                    MY0.eduDescription,
                    Literal(edu.get("description", ""), datatype=XSD.string),
                )
            )
        if edu.get("degree"):
            deg_uri = URIRef(
                f"http://example.com/data/degree_{sanitize_uri_string(edu['degree'])}"
            )
            g.add((edu_uri, MY0.degree, deg_uri))
            g.add((deg_uri, RDF.type, MYVALUE0.EduDegree))
            g.add((deg_uri, RDFS.label, Literal(edu["degree"], datatype=XSD.string)))

    for idx, crs in enumerate(candidate_data.get("courses", [])):
        crs_uri = URIRef(f"http://example.com/data/course_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasCourse, crs_uri))
        g.add((crs_uri, RDF.type, MY0.Course))
        g.add(
            (
                crs_uri,
                MY0.courseTitle,
                Literal(crs.get("title", ""), datatype=XSD.string),
            )
        )
        g.add(
            (
                crs_uri,
                MY0.hasCertification,
                Literal(crs.get("has_certification", False), datatype=XSD.boolean),
            )
        )
        if crs.get("description"):
            g.add(
                (
                    crs_uri,
                    MY0.courseDescription,
                    Literal(crs.get("description", ""), datatype=XSD.string),
                )
            )
        if crs.get("url"):
            g.add(
                (
                    crs_uri,
                    MY0.courseURL,
                    Literal(crs.get("url", ""), datatype=XSD.string),
                )
            )
        if crs.get("start_date"):
            g.add(
                (
                    crs_uri,
                    MY0.courseStartDate,
                    Literal(crs.get("start_date", ""), datatype=XSD.string),
                )
            )
        if crs.get("finish_date"):
            g.add(
                (
                    crs_uri,
                    MY0.courseFinishDate,
                    Literal(crs.get("finish_date", ""), datatype=XSD.string),
                )
            )
        if crs.get("organized_by"):
            org_uri = URIRef(
                f"http://example.com/data/org_{sanitize_uri_string(crs['organized_by'])}"
            )
            g.add((crs_uri, MY0.organizedBy, org_uri))
            g.add((org_uri, RDF.type, MY0.Organization))
            g.add(
                (
                    org_uri,
                    MY0.orgName,
                    Literal(crs["organized_by"], datatype=XSD.string),
                )
            )

    for idx, pat in enumerate(candidate_data.get("patents", [])):
        pat_uri = URIRef(f"http://example.com/data/patent_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasPatent, pat_uri))
        g.add((pat_uri, RDF.type, MY0.Patent))
        g.add(
            (
                pat_uri,
                MY0.patentTitle,
                Literal(pat.get("title", ""), datatype=XSD.string),
            )
        )
        if pat.get("office"):
            g.add(
                (
                    pat_uri,
                    MY0.patentOffice,
                    Literal(pat.get("office", ""), datatype=XSD.string),
                )
            )
        if pat.get("number"):
            g.add(
                (
                    pat_uri,
                    MY0.patentNumber,
                    Literal(pat.get("number", ""), datatype=XSD.string),
                )
            )
        if pat.get("inventor"):
            g.add(
                (
                    pat_uri,
                    MY0.patentInventor,
                    Literal(pat.get("inventor", ""), datatype=XSD.string),
                )
            )
        if pat.get("url"):
            g.add(
                (
                    pat_uri,
                    MY0.patentURL,
                    Literal(pat.get("url", ""), datatype=XSD.string),
                )
            )
        if pat.get("description"):
            g.add(
                (
                    pat_uri,
                    MY0.patentDescription,
                    Literal(pat.get("description", ""), datatype=XSD.string),
                )
            )
        if pat.get("issued_date"):
            g.add(
                (
                    pat_uri,
                    MY0.patentIssuedDate,
                    Literal(pat.get("issued_date", ""), datatype=XSD.string),
                )
            )
        if pat.get("status"):
            stat_uri = URIRef(
                f"http://example.com/data/patstatus_{sanitize_uri_string(pat['status'])}"
            )
            g.add((pat_uri, MY0.patentStatus, stat_uri))
            g.add((stat_uri, RDF.type, MYVALUE0.StatusProperty))
            g.add((stat_uri, RDFS.label, Literal(pat["status"], datatype=XSD.string)))

    for idx, proj in enumerate(candidate_data.get("projects", [])):
        proj_uri = URIRef(f"http://example.com/data/proj_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasProject, proj_uri))
        g.add((proj_uri, RDF.type, MY0.Project))
        g.add(
            (
                proj_uri,
                MY0.projectName,
                Literal(proj.get("name", ""), datatype=XSD.string),
            )
        )
        g.add(
            (
                proj_uri,
                MY0.projectIsCurrent,
                Literal(proj.get("is_current", False), datatype=XSD.boolean),
            )
        )
        if proj.get("role"):
            g.add(
                (
                    proj_uri,
                    MY0.projectRole,
                    Literal(proj.get("role", ""), datatype=XSD.string),
                )
            )
        if proj.get("start_date"):
            g.add(
                (
                    proj_uri,
                    MY0.projectStartDate,
                    Literal(proj.get("start_date", ""), datatype=XSD.string),
                )
            )
        if proj.get("end_date"):
            g.add(
                (
                    proj_uri,
                    MY0.projectEndDate,
                    Literal(proj.get("end_date", ""), datatype=XSD.string),
                )
            )
        if proj.get("creator"):
            g.add(
                (
                    proj_uri,
                    MY0.projectCreator,
                    Literal(proj.get("creator", ""), datatype=XSD.string),
                )
            )
        if proj.get("url"):
            g.add(
                (
                    proj_uri,
                    MY0.projectURL,
                    Literal(proj.get("url", ""), datatype=XSD.string),
                )
            )
        if proj.get("description"):
            g.add(
                (
                    proj_uri,
                    MY0.projectDescription,
                    Literal(proj.get("description", ""), datatype=XSD.string),
                )
            )

    for skill_dict in candidate_data.get("technical_skills", []):
        skill_name = skill_dict.get("name", "")
        esco_data = skill_dict.get("esco_data")

        if esco_data and esco_data.get("uri"):
            # link the CV directly to the ESCO URI
            esco_uri = URIRef(esco_data["uri"])
            g.add((cv_uri, MY0.hasSkill, esco_uri))
            g.add((esco_uri, MY0.skillName, Literal(skill_name, datatype=XSD.string)))

            # materialize the parent hierarchy
            for parent_label in esco_data.get("parents", []):
                parent_uri = URIRef(
                    f"http://example.com/data/category_{sanitize_uri_string(parent_label)}"
                )
                # link the ESCO skill to its parent category
                g.add((esco_uri, SKOS.broader, parent_uri))
                g.add((parent_uri, RDF.type, SKOS.Concept))
                g.add(
                    (parent_uri, RDFS.label, Literal(parent_label, datatype=XSD.string))
                )

        else:
            # unmapped/custom skill
            custom_skill_uri = URIRef(
                f"http://example.com/data/custom_skill_{candidate_slug}_{sanitize_uri_string(skill_name)}"
            )
            g.add((cv_uri, MY0.hasSkill, custom_skill_uri))
            g.add((custom_skill_uri, RDF.type, MY0.Skill))
            g.add(
                (
                    custom_skill_uri,
                    MY0.skillName,
                    Literal(skill_name, datatype=XSD.string),
                )
            )

    for idx, lang in enumerate(candidate_data.get("languages", [])):
        lang_uri = URIRef(f"http://example.com/data/lang_{candidate_slug}_{idx}")
        g.add((person_uri, MY0.hasSkill, lang_uri))
        g.add((lang_uri, RDF.type, MY0.LanguageSkill))
        g.add(
            (
                lang_uri,
                MY0.skillName,
                Literal(lang.get("name", ""), datatype=XSD.string),
            )
        )
        if lang.get("proficiency"):
            prof_uri = URIRef(
                f"http://example.com/data/prof_{sanitize_uri_string(lang['proficiency'])}"
            )
            g.add((lang_uri, MY0.languageSkillProficiency, prof_uri))
            g.add((prof_uri, RDF.type, MYVALUE0.LanguageSkillProficiencyProperty))
            g.add(
                (
                    prof_uri,
                    RDFS.label,
                    Literal(lang["proficiency"], datatype=XSD.string),
                )
            )

    target_data = candidate_data.get("target")
    if target_data:
        target_uri = URIRef(f"http://example.com/data/target_{candidate_slug}")
        g.add((cv_uri, MY0.hasTarget, target_uri))
        g.add((target_uri, RDF.type, MY0.Target))
        g.add(
            (
                target_uri,
                MY0.targetJobTitle,
                Literal(target_data.get("job_title", ""), datatype=XSD.string),
            )
        )
        g.add(
            (
                target_uri,
                MY0.targetConditionWillRelocate,
                Literal(target_data.get("relocate", False), datatype=XSD.boolean),
            )
        )
        g.add(
            (
                target_uri,
                MY0.targetConditionWillTravel,
                Literal(target_data.get("travel", False), datatype=XSD.boolean),
            )
        )

    addr = candidate_data.get("address")
    if addr:
        addr_uri = URIRef(f"http://example.com/data/addr_{candidate_slug}")
        g.add((person_uri, MY0.hasAddress, addr_uri))
        g.add((addr_uri, RDF.type, MY0.Address))
        g.add((addr_uri, MY0.city, Literal(addr.get("city", ""), datatype=XSD.string)))
        g.add(
            (
                addr_uri,
                MY0.country,
                Literal(addr.get("country", ""), datatype=XSD.string),
            )
        )

    for idx, site in enumerate(candidate_data.get("websites", [])):
        site_uri = URIRef(f"http://example.com/data/site_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasWebsite, site_uri))
        g.add((site_uri, RDF.type, MY0.Website))
        g.add((site_uri, MY0.websiteURL, Literal(site.get("url", ""))))
        g.add((site_uri, MY0.websiteType, Literal(site.get("website_type", ""))))

    for idx, im in enumerate(candidate_data.get("instant_messaging", [])):
        im_uri = URIRef(f"http://example.com/data/im_{candidate_slug}_{idx}")
        g.add((person_uri, MY0.hasInstantMessaging, im_uri))
        g.add((im_uri, RDF.type, MY0.InstantMessaging))
        g.add(
            (
                im_uri,
                MY0.instantMessagingUsername,
                Literal(im.get("username", ""), datatype=XSD.string),
            )
        )
        im_type_uri = URIRef(
            f"http://example.com/data/imtype_{sanitize_uri_string(im['name'])}"
        )
        g.add((im_uri, MY0.instantMessagingName, im_type_uri))
        g.add((im_type_uri, RDF.type, MYVALUE0.InstantMessagingTypeProperty))
        g.add((im_type_uri, RDFS.label, Literal(im["name"], datatype=XSD.string)))

    for idx, info in enumerate(candidate_data.get("other_info", [])):
        info_uri = URIRef(f"http://example.com/data/other_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasOtherInfo, info_uri))
        g.add((info_uri, RDF.type, MY0.OtherInfo))
        g.add(
            (
                info_uri,
                MY0.otherInfoDescription,
                Literal(info.get("description", ""), datatype=XSD.string),
            )
        )
        info_type_uri = URIRef(
            f"http://example.com/data/othertype_{sanitize_uri_string(info['type'])}"
        )
        g.add((info_uri, MY0.otherInfoType, info_type_uri))
        g.add((info_type_uri, RDF.type, MYVALUE0.OtherCVInfoType))
        g.add((info_type_uri, RDFS.label, Literal(info["type"], datatype=XSD.string)))

    return g


def upload_to_graphdb(graph: Graph):
    cv_uri = next(graph.subjects(RDF.type, MY0.CV), None)
    if not cv_uri:
        return
    named_graph_id = str(cv_uri)
    nt_data = graph.serialize(format="nt")
    sparql_query = f"CLEAR GRAPH <{named_graph_id}>; INSERT DATA {{ GRAPH <{named_graph_id}> {{ {nt_data} }} }}"
    sparql = SPARQLWrapper(GRAPHDB_URL)
    sparql.setMethod(POST)
    sparql.setQuery(sparql_query)
    sparql.query()
