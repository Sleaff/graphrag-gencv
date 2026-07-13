import re
from typing import Optional

from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDFS, SKOS, XSD
from SPARQLWrapper import POST, SPARQLWrapper

from settings import GRAPHDB_URL

MY0 = Namespace("http://example.com/resume2rdf_ontology.rdf#")
MYVALUE0 = Namespace("http://example.com/resume2rdf_value_ontology.rdf#")
ESCO = Namespace("http://data.europa.eu/esco/model#")
COUNTRY = Namespace("http://www.bpiresearch.com/BPMO/2004/03/03/cdl/Countries#")
DATA = "http://example.com/data/"
GRAPHDB_STATEMENTS_URL = (
    GRAPHDB_URL.rstrip("/")
    if GRAPHDB_URL.rstrip("/").endswith("/statements")
    else GRAPHDB_URL.rstrip("/") + "/statements"
)


def sanitize_uri_string(text: str) -> str:
    if not text:
        return "unknown"
    sanitized = re.sub(
        r"[^a-z0-9_\-]", "", text.lower().strip().replace(" ", "_")
    )
    return sanitized or "unknown"


def add_literal(
    graph: Graph,
    subject: URIRef,
    predicate: URIRef,
    value,
    datatype=XSD.string,
) -> None:
    if value is None:
        return
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return
    graph.add((subject, predicate, Literal(value, datatype=datatype)))


def create_controlled_value(
    graph: Graph,
    value: Optional[str],
    uri_prefix: str,
    rdf_type: URIRef,
) -> Optional[URIRef]:
    if not value or not value.strip():
        return None
    value_uri = URIRef(
        f"{DATA}{uri_prefix}_{sanitize_uri_string(value)}"
    )
    graph.add((value_uri, RDF.type, rdf_type))
    graph.add((value_uri, RDFS.label, Literal(value, datatype=XSD.string)))
    return value_uri


def create_country(graph: Graph, country_name: Optional[str]) -> Optional[URIRef]:
    if not country_name or not country_name.strip():
        return None
    country_uri = URIRef(
        f"{COUNTRY}{sanitize_uri_string(country_name)}"
    )
    graph.add((country_uri, RDF.type, COUNTRY.ISO3166DefinedCountry))
    graph.add(
        (country_uri, RDFS.label, Literal(country_name, datatype=XSD.string))
    )
    return country_uri


def add_address(
    graph: Graph,
    owner_uri: URIRef,
    predicate: URIRef,
    address: Optional[dict],
    address_uri: URIRef,
) -> None:
    if not address or not any(address.values()):
        return

    graph.add((owner_uri, predicate, address_uri))
    graph.add((address_uri, RDF.type, MY0.Address))
    add_literal(graph, address_uri, MY0.city, address.get("city"))
    add_literal(graph, address_uri, MY0.street, address.get("street"))
    add_literal(graph, address_uri, MY0.postalCode, address.get("postal_code"))

    country_uri = create_country(graph, address.get("country"))
    if country_uri:
        graph.add((address_uri, MY0.country, country_uri))


def add_vector_reference(graph: Graph, entity_uri: URIRef, item: dict) -> None:
    add_literal(
        graph,
        entity_uri,
        MY0.hasVectorReference,
        item.get("vector_id"),
    )


def add_skill(
    graph: Graph,
    owner_uri: URIRef,
    candidate_slug: str,
    skill_dict: dict,
) -> None:
    skill_name = skill_dict.get("name", "")
    if not skill_name:
        return

    esco_data = skill_dict.get("esco_data") or {}
    if esco_data.get("uri"):
        skill_uri = URIRef(esco_data["uri"])
        graph.add((skill_uri, RDF.type, ESCO.Skill))
    else:
        skill_uri = URIRef(
            f"{DATA}custom_skill_{candidate_slug}_{sanitize_uri_string(skill_name)}"
        )
        graph.add((skill_uri, RDF.type, MY0.Skill))

    graph.add((owner_uri, MY0.hasSkill, skill_uri))
    graph.add(
        (skill_uri, MY0.skillName, Literal(skill_name, datatype=XSD.string))
    )

    for parent_label in esco_data.get("parents", []):
        parent_uri = URIRef(
            f"{DATA}category_{sanitize_uri_string(parent_label)}"
        )
        graph.add((skill_uri, SKOS.broader, parent_uri))
        graph.add((parent_uri, RDF.type, SKOS.Concept))
        graph.add(
            (parent_uri, RDFS.label, Literal(parent_label, datatype=XSD.string))
        )


def create_rdf_graph(candidate_data: dict) -> Graph:
    graph = Graph()
    graph.bind("my0", MY0)
    graph.bind("myvalue0", MYVALUE0)
    graph.bind("esco", ESCO)
    graph.bind("country", COUNTRY)
    graph.bind("skos", SKOS)

    candidate_name = candidate_data.get("name", "Unknown")
    candidate_slug = sanitize_uri_string(candidate_name)
    cv_uri = URIRef(f"{DATA}cv_{candidate_slug}")
    person_uri = URIRef(f"{DATA}person_{candidate_slug}")

    graph.add((cv_uri, RDF.type, MY0.CV))
    graph.add((cv_uri, MY0.aboutPerson, person_uri))
    graph.add((person_uri, RDF.type, MY0.Person))
    add_literal(graph, person_uri, MY0.firstName, candidate_name)

    gender_uri = create_controlled_value(
        graph,
        candidate_data.get("gender"),
        "gender",
        MYVALUE0.GenderProperty,
    )
    if gender_uri:
        graph.add((person_uri, MY0.gender, gender_uri))

    nationality_uri = create_country(graph, candidate_data.get("nationality"))
    if nationality_uri:
        graph.add((person_uri, MY0.hasNationality, nationality_uri))

    add_literal(graph, person_uri, MY0.dateOfBirth, candidate_data.get("date_of_birth"))
    add_literal(graph, person_uri, MY0.driversLicence, candidate_data.get("drivers_licence"))
    add_literal(graph, person_uri, MY0.personShortDescription, candidate_data.get("short_description"))
    add_literal(graph, person_uri, MY0.personLongDescription, candidate_data.get("long_description"))
    add_literal(graph, person_uri, MY0.email, candidate_data.get("email"))
    add_literal(graph, person_uri, MY0.phoneNumberMobile, candidate_data.get("phone_mobile"))
    add_literal(graph, person_uri, MY0.phoneNumberHome, candidate_data.get("phone_home"))
    add_literal(graph, person_uri, MY0.phoneNumberWork, candidate_data.get("phone_work"))

    add_address(
        graph,
        person_uri,
        MY0.address,
        candidate_data.get("address"),
        URIRef(f"{DATA}addr_{candidate_slug}"),
    )

    for idx, job in enumerate(candidate_data.get("jobs", [])):
        work_uri = URIRef(f"{DATA}work_{candidate_slug}_{idx}")
        company_name = job.get("company", "Unknown")
        company_uri = URIRef(
            f"{DATA}comp_{candidate_slug}_{idx}_{sanitize_uri_string(company_name)}"
        )

        graph.add((cv_uri, MY0.hasWorkHistory, work_uri))
        graph.add((work_uri, RDF.type, MY0.WorkHistory))
        graph.add((work_uri, MY0.employedIn, company_uri))
        graph.add((company_uri, RDF.type, MY0.Company))
        add_literal(graph, company_uri, MY0.orgName, company_name)
        add_literal(graph, work_uri, MY0.jobTitle, job.get("title"))
        add_literal(graph, work_uri, MY0.startDate, job.get("start"))
        add_literal(graph, work_uri, MY0.endDate, job.get("end"))
        add_literal(graph, work_uri, MY0.jobDescription, job.get("description"))
        graph.add(
            (
                work_uri,
                MY0.isCurrent,
                Literal(job.get("is_current", False), datatype=XSD.boolean),
            )
        )

        add_address(
            graph,
            company_uri,
            MY0.orgAddress,
            job.get("address"),
            URIRef(f"{DATA}addr_comp_{candidate_slug}_{idx}"),
        )

        career_level_uri = create_controlled_value(
            graph,
            job.get("career_level"),
            "careerlevel",
            MYVALUE0.CVCareerLevel,
        )
        if career_level_uri:
            graph.add((work_uri, MY0.careerLevel, career_level_uri))

        job_type_uri = create_controlled_value(
            graph,
            job.get("job_type"),
            "jobtype",
            MYVALUE0.CVEmploymentType,
        )
        if job_type_uri:
            graph.add((work_uri, MY0.jobType, job_type_uri))

        for skill_dict in job.get("esco_skills", []):
            add_skill(graph, work_uri, candidate_slug, skill_dict)

        add_vector_reference(graph, work_uri, job)

    for idx, edu in enumerate(candidate_data.get("education", [])):
        edu_uri = URIRef(f"{DATA}edu_{candidate_slug}_{idx}")
        org_uri = URIRef(
            f"{DATA}uni_{candidate_slug}_{idx}_{sanitize_uri_string(edu.get('institution', ''))}"
        )

        graph.add((cv_uri, MY0.hasEducation, edu_uri))
        graph.add((edu_uri, RDF.type, MY0.Education))
        graph.add((edu_uri, MY0.studiedIn, org_uri))
        graph.add((org_uri, RDF.type, MY0.EducationalOrg))
        add_literal(graph, org_uri, MY0.orgName, edu.get("institution"))
        add_literal(graph, edu_uri, MY0.degreeFieldOfStudy, edu.get("field_of_study"))
        add_literal(graph, edu_uri, MY0.eduStartDate, edu.get("start_date"))
        add_literal(graph, edu_uri, MY0.eduGradDate, edu.get("end_date"))
        add_literal(graph, edu_uri, MY0.eduDescription, edu.get("description"))

        degree_uri = create_controlled_value(
            graph,
            edu.get("degree"),
            "degree",
            MYVALUE0.EduDegree,
        )
        if degree_uri:
            graph.add((edu_uri, MY0.degree, degree_uri))

        add_vector_reference(graph, edu_uri, edu)

    for idx, crs in enumerate(candidate_data.get("courses", [])):
        crs_uri = URIRef(f"{DATA}course_{candidate_slug}_{idx}")
        graph.add((cv_uri, MY0.hasCourse, crs_uri))
        graph.add((crs_uri, RDF.type, MY0.Course))
        add_literal(graph, crs_uri, MY0.courseTitle, crs.get("title"))
        add_literal(graph, crs_uri, MY0.courseDescription, crs.get("description"))
        add_literal(graph, crs_uri, MY0.courseURL, crs.get("url"))
        add_literal(graph, crs_uri, MY0.courseStartDate, crs.get("start_date"))
        add_literal(graph, crs_uri, MY0.courseFinishDate, crs.get("finish_date"))
        graph.add(
            (
                crs_uri,
                MY0.hasCertification,
                Literal(crs.get("has_certification", False), datatype=XSD.boolean),
            )
        )

        if crs.get("organized_by"):
            org_uri = URIRef(
                f"{DATA}org_{sanitize_uri_string(crs['organized_by'])}"
            )
            graph.add((crs_uri, MY0.organizedBy, org_uri))
            graph.add((org_uri, RDF.type, MY0.Organization))
            add_literal(graph, org_uri, MY0.orgName, crs.get("organized_by"))

        add_vector_reference(graph, crs_uri, crs)

    for idx, pat in enumerate(candidate_data.get("patents", [])):
        pat_uri = URIRef(f"{DATA}patent_{candidate_slug}_{idx}")
        graph.add((cv_uri, MY0.hasPatent, pat_uri))
        graph.add((pat_uri, RDF.type, MY0.Patent))
        add_literal(graph, pat_uri, MY0.patentTitle, pat.get("title"))
        add_literal(graph, pat_uri, MY0.patentOffice, pat.get("office"))
        add_literal(graph, pat_uri, MY0.patentNumber, pat.get("number"))
        add_literal(graph, pat_uri, MY0.patentInventor, pat.get("inventor"))
        add_literal(graph, pat_uri, MY0.patentURL, pat.get("url"))
        add_literal(graph, pat_uri, MY0.patentDescription, pat.get("description"))
        add_literal(graph, pat_uri, MY0.patentIssuedDate, pat.get("issued_date"))

        status_uri = create_controlled_value(
            graph,
            pat.get("status"),
            "patstatus",
            MYVALUE0.StatusProperty,
        )
        if status_uri:
            graph.add((pat_uri, MY0.patentStatus, status_uri))

        add_vector_reference(graph, pat_uri, pat)

    for idx, proj in enumerate(candidate_data.get("projects", [])):
        proj_uri = URIRef(f"{DATA}proj_{candidate_slug}_{idx}")
        graph.add((cv_uri, MY0.hasProject, proj_uri))
        graph.add((proj_uri, RDF.type, MY0.Project))
        add_literal(graph, proj_uri, MY0.projectName, proj.get("name"))
        add_literal(graph, proj_uri, MY0.projectRole, proj.get("role"))
        add_literal(graph, proj_uri, MY0.projectStartDate, proj.get("start_date"))
        add_literal(graph, proj_uri, MY0.projectEndDate, proj.get("end_date"))
        add_literal(graph, proj_uri, MY0.projectCreator, proj.get("creator"))
        add_literal(graph, proj_uri, MY0.projectURL, proj.get("url"))
        add_literal(graph, proj_uri, MY0.projectDescription, proj.get("description"))
        graph.add(
            (
                proj_uri,
                MY0.projectIsCurrent,
                Literal(proj.get("is_current", False), datatype=XSD.boolean),
            )
        )
        add_vector_reference(graph, proj_uri, proj)

    for skill_dict in candidate_data.get("technical_skills", []):
        add_skill(graph, cv_uri, candidate_slug, skill_dict)

    for idx, lang in enumerate(candidate_data.get("languages", [])):
        lang_uri = URIRef(f"{DATA}lang_{candidate_slug}_{idx}")
        graph.add((person_uri, MY0.hasSkill, lang_uri))
        graph.add((lang_uri, RDF.type, MY0.LanguageSkill))
        add_literal(graph, lang_uri, MY0.skillName, lang.get("name"))

        proficiency_uri = create_controlled_value(
            graph,
            lang.get("proficiency"),
            "prof",
            MYVALUE0.LanguageSkillProficiencyProperty,
        )
        if proficiency_uri:
            graph.add((lang_uri, MY0.languageSkillProficiency, proficiency_uri))

    target_data = candidate_data.get("target")
    if target_data:
        target_uri = URIRef(f"{DATA}target_{candidate_slug}")
        graph.add((cv_uri, MY0.hasTarget, target_uri))
        graph.add((target_uri, RDF.type, MY0.Target))
        add_literal(graph, target_uri, MY0.targetJobTitle, target_data.get("job_title"))
        graph.add(
            (
                target_uri,
                MY0.targetConditionWillRelocate,
                Literal(target_data.get("relocate", False), datatype=XSD.boolean),
            )
        )
        graph.add(
            (
                target_uri,
                MY0.targetConditionWillTravel,
                Literal(target_data.get("travel", False), datatype=XSD.boolean),
            )
        )

        target_type_uri = create_controlled_value(
            graph,
            target_data.get("job_mode"),
            "target_jobtype",
            MYVALUE0.CVEmploymentType,
        )
        if target_type_uri:
            graph.add((target_uri, MY0.targetJobType, target_type_uri))

    for idx, site in enumerate(candidate_data.get("websites", [])):
        site_uri = URIRef(f"{DATA}site_{candidate_slug}_{idx}")
        graph.add((person_uri, MY0.hasWebsite, site_uri))
        graph.add((site_uri, RDF.type, MY0.Website))
        add_literal(graph, site_uri, MY0.websiteURL, site.get("url"))

        site_type_uri = create_controlled_value(
            graph,
            site.get("website_type"),
            "websitetype",
            MYVALUE0.WebsiteTypeProperty,
        )
        if site_type_uri:
            graph.add((site_uri, MY0.websiteType, site_type_uri))

    for idx, im in enumerate(candidate_data.get("instant_messaging", [])):
        im_uri = URIRef(f"{DATA}im_{candidate_slug}_{idx}")
        graph.add((person_uri, MY0.hasInstantMessaging, im_uri))
        graph.add((im_uri, RDF.type, MY0.InstantMessaging))
        add_literal(graph, im_uri, MY0.instantMessagingUsername, im.get("username"))

        im_type_uri = create_controlled_value(
            graph,
            im.get("name"),
            "imtype",
            MYVALUE0.InstantMessagingTypeProperty,
        )
        if im_type_uri:
            graph.add((im_uri, MY0.instantMessagingName, im_type_uri))

    for idx, honor in enumerate(candidate_data.get("honors", [])):
        honor_uri = URIRef(f"{DATA}honor_{candidate_slug}_{idx}")
        graph.add((cv_uri, MY0.hasHonorAward, honor_uri))
        graph.add((honor_uri, RDF.type, MY0.HonorAward))
        add_literal(graph, honor_uri, MY0.honorTitle, honor.get("title"))
        add_literal(graph, honor_uri, MY0.honorIssuer, honor.get("issuer"))
        add_literal(graph, honor_uri, MY0.honorIssuedDate, honor.get("date"))

    for idx, publication in enumerate(candidate_data.get("publications", [])):
        publication_uri = URIRef(f"{DATA}publication_{candidate_slug}_{idx}")
        graph.add((cv_uri, MY0.hasPublication, publication_uri))
        graph.add((publication_uri, RDF.type, MY0.Publication))
        add_literal(graph, publication_uri, MY0.publicationTitle, publication.get("title"))
        add_literal(graph, publication_uri, MY0.publicationPublisher, publication.get("publisher"))
        add_literal(graph, publication_uri, MY0.publicationDate, publication.get("date"))
        add_literal(graph, publication_uri, MY0.publicationDescription, publication.get("description"))
        add_vector_reference(graph, publication_uri, publication)

    for idx, reference in enumerate(candidate_data.get("references", [])):
        reference_uri = URIRef(f"{DATA}reference_{candidate_slug}_{idx}")
        reference_person_uri = URIRef(
            f"{DATA}reference_person_{candidate_slug}_{idx}"
        )
        graph.add((cv_uri, MY0.hasReference, reference_uri))
        graph.add((reference_uri, RDF.type, MY0.Reference))
        graph.add((reference_uri, MY0.referenceBy, reference_person_uri))
        graph.add((reference_person_uri, RDF.type, MY0.Person))
        add_literal(graph, reference_person_uri, MY0.firstName, reference.get("name"))
        add_literal(
            graph,
            reference_uri,
            MY0.refRelationDescription,
            reference.get("relation"),
        )

    for idx, info in enumerate(candidate_data.get("other_info", [])):
        info_uri = URIRef(f"{DATA}other_{candidate_slug}_{idx}")
        graph.add((cv_uri, MY0.hasOtherInfo, info_uri))
        graph.add((info_uri, RDF.type, MY0.OtherInfo))
        add_literal(graph, info_uri, MY0.otherInfoDescription, info.get("description"))

        info_type_uri = create_controlled_value(
            graph,
            info.get("type"),
            "othertype",
            MYVALUE0.OtherCVInfoType,
        )
        if info_type_uri:
            graph.add((info_uri, MY0.otherInfoType, info_type_uri))

    return graph


def upload_to_graphdb(graph: Graph):
    cv_uri = next(graph.subjects(RDF.type, MY0.CV), None)
    if not cv_uri:
        raise ValueError("RDF graph does not contain a CV resource.")

    named_graph_id = str(cv_uri)
    nt_data = graph.serialize(format="nt")
    sparql_query = (
        f"CLEAR GRAPH <{named_graph_id}>; "
        f"INSERT DATA {{ GRAPH <{named_graph_id}> {{ {nt_data} }} }}"
    )
    sparql = SPARQLWrapper(GRAPHDB_STATEMENTS_URL)
    sparql.setMethod(POST)
    sparql.setQuery(sparql_query)
    sparql.query()
