import json

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import RDFS, SKOS
from SPARQLWrapper import JSON, POST, SPARQLWrapper

from settings import GRAPHDB_URL

MY0 = Namespace("http://example.com/resume2rdf_ontology.rdf#")


def sparql_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def run_select(query: str) -> list[dict]:
    sparql = SPARQLWrapper(GRAPHDB_URL)
    sparql.setMethod(POST)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    response = sparql.query().convert()
    return response["results"]["bindings"]


def binding_to_term(binding: dict):
    binding_type = binding.get("type")
    value = binding["value"]
    if binding_type == "uri":
        return URIRef(value)
    if binding_type == "bnode":
        return BNode(value)
    datatype = URIRef(binding["datatype"]) if binding.get("datatype") else None
    return Literal(value, lang=binding.get("xml:lang"), datatype=datatype)


def find_candidate_graph(candidate_name: str) -> tuple[URIRef, URIRef, URIRef]:
    query = f"""
    PREFIX my0: <http://example.com/resume2rdf_ontology.rdf#>
    SELECT DISTINCT ?graph ?cv ?person WHERE {{
        GRAPH ?graph {{
            ?cv a my0:CV ;
                my0:aboutPerson ?person .
            ?person my0:fullName {sparql_string(candidate_name)} .
        }}
    }}
    LIMIT 1
    """
    rows = run_select(query)
    if not rows:
        raise LookupError(f"Candidate not found: {candidate_name}")

    row = rows[0]
    return (
        URIRef(row["graph"]["value"]),
        URIRef(row["cv"]["value"]),
        URIRef(row["person"]["value"]),
    )


def load_named_graph(graph_uri: URIRef) -> Graph:
    rows = run_select(
        f"SELECT ?s ?p ?o WHERE {{ GRAPH <{graph_uri}> {{ ?s ?p ?o }} }}"
    )
    graph = Graph()
    for row in rows:
        graph.add(
            (
                binding_to_term(row["s"]),
                binding_to_term(row["p"]),
                binding_to_term(row["o"]),
            )
        )
    return graph


def get_value(graph: Graph, subject, predicate, default: str = "") -> str:
    value = graph.value(subject, predicate)
    return str(value) if value is not None else default


def get_boolean(
    graph: Graph,
    subject,
    predicate,
    default: bool = False,
) -> bool:
    value = graph.value(subject, predicate)
    if value is None:
        return default
    if isinstance(value, Literal):
        converted = value.toPython()
        if isinstance(converted, bool):
            return converted
    return str(value).strip().lower() in {"true", "1", "yes"}


def get_label(graph: Graph, resource, default: str = "") -> str:
    if resource is None:
        return default
    return get_value(graph, resource, RDFS.label, default or str(resource))


def get_country_name(graph: Graph, address_uri) -> str:
    country_uri = graph.value(address_uri, MY0.country)
    if country_uri is None:
        return ""
    country_label = graph.value(country_uri, RDFS.label)
    if country_label is not None:
        return str(country_label)
    return str(country_uri).rsplit("#", 1)[-1]


def get_address(graph: Graph, address_uri):
    if address_uri is None:
        return None
    address = {
        "city": get_value(graph, address_uri, MY0.city),
        "country": get_country_name(graph, address_uri),
        "street": get_value(graph, address_uri, MY0.street),
        "postal_code": get_value(graph, address_uri, MY0.postalCode),
    }
    return address if any(address.values()) else None


def get_vector_id(graph: Graph, entity_uri) -> str:
    return get_value(graph, entity_uri, MY0.hasVectorReference)


def get_skills(graph: Graph, owner_uri) -> list[dict]:
    skills = []
    for skill_uri in graph.objects(owner_uri, MY0.hasSkill):
        if (skill_uri, RDF.type, MY0.LanguageSkill) in graph:
            continue

        skill_name = get_value(graph, skill_uri, MY0.skillName)
        if not skill_name:
            skill_name = str(skill_uri).rsplit("/", 1)[-1]

        parents = sorted(
            {
                get_label(graph, parent_uri)
                for parent_uri in graph.objects(skill_uri, SKOS.broader)
                if get_label(graph, parent_uri)
            }
        )
        skills.append(
            {
                "name": skill_name,
                "parents": parents,
            }
        )

    return sorted(skills, key=lambda item: item["name"].casefold())


def get_candidate_profile(candidate_name: str):
    graph_uri, cv_uri, person_uri = find_candidate_graph(candidate_name)
    graph = load_named_graph(graph_uri)

    gender_uri = graph.value(person_uri, MY0.gender)
    nationality_uri = graph.value(person_uri, MY0.hasNationality)
    nationality = get_label(graph, nationality_uri, "")
    if not nationality and nationality_uri:
        nationality = str(nationality_uri).rsplit("#", 1)[-1]

    jobs = []
    for work_uri in graph.objects(cv_uri, MY0.hasWorkHistory):
        company_uri = graph.value(work_uri, MY0.employedIn)
        company_address_uri = (
            graph.value(company_uri, MY0.orgAddress)
            if company_uri is not None
            else None
        )
        jobs.append(
            {
                "title": get_value(graph, work_uri, MY0.jobTitle),
                "company": get_value(graph, company_uri, MY0.orgName)
                if company_uri
                else "",
                "start": get_value(graph, work_uri, MY0.startDate),
                "end": get_value(graph, work_uri, MY0.endDate),
                "description": get_value(graph, work_uri, MY0.jobDescription),
                "is_current": get_boolean(graph, work_uri, MY0.isCurrent),
                "career_level": get_label(
                    graph,
                    graph.value(work_uri, MY0.careerLevel),
                    "",
                ),
                "job_type": get_label(
                    graph,
                    graph.value(work_uri, MY0.jobType),
                    "",
                ),
                "address": get_address(graph, company_address_uri),
                "raw_skills": get_skills(graph, work_uri),
                # "vector_id": get_vector_id(graph, work_uri),
            }
        )

    education = []
    for edu_uri in graph.objects(cv_uri, MY0.hasEducation):
        institution_uri = graph.value(edu_uri, MY0.studiedIn)
        degree_uri = graph.value(edu_uri, MY0.degree)
        education.append(
            {
                "degree": get_label(graph, degree_uri, ""),
                "institution": get_value(graph, institution_uri, MY0.orgName)
                if institution_uri
                else "",
                "start_date": get_value(graph, edu_uri, MY0.eduStartDate),
                "end_date": get_value(graph, edu_uri, MY0.eduGradDate),
                "field_of_study": get_value(
                    graph,
                    edu_uri,
                    MY0.degreeFieldOfStudy,
                ),
                "description": get_value(graph, edu_uri, MY0.eduDescription),
                # "vector_id": get_vector_id(graph, edu_uri),
            }
        )

    courses = []
    for course_uri in graph.objects(cv_uri, MY0.hasCourse):
        organizer_uri = graph.value(course_uri, MY0.organizedBy)
        courses.append(
            {
                "title": get_value(graph, course_uri, MY0.courseTitle),
                "description": get_value(
                    graph,
                    course_uri,
                    MY0.courseDescription,
                ),
                "url": get_value(graph, course_uri, MY0.courseURL),
                "start_date": get_value(
                    graph,
                    course_uri,
                    MY0.courseStartDate,
                ),
                "finish_date": get_value(
                    graph,
                    course_uri,
                    MY0.courseFinishDate,
                ),
                "has_certification": get_boolean(
                    graph,
                    course_uri,
                    MY0.hasCertification,
                ),
                "organized_by": get_value(graph, organizer_uri, MY0.orgName)
                if organizer_uri
                else "",
                # "vector_id": get_vector_id(graph, course_uri),
            }
        )

    patents = []
    for patent_uri in graph.objects(cv_uri, MY0.hasPatent):
        patents.append(
            {
                "title": get_value(graph, patent_uri, MY0.patentTitle),
                "office": get_value(graph, patent_uri, MY0.patentOffice),
                "number": get_value(graph, patent_uri, MY0.patentNumber),
                "inventor": get_value(graph, patent_uri, MY0.patentInventor),
                "url": get_value(graph, patent_uri, MY0.patentURL),
                "description": get_value(
                    graph,
                    patent_uri,
                    MY0.patentDescription,
                ),
                "issued_date": get_value(
                    graph,
                    patent_uri,
                    MY0.patentIssuedDate,
                ),
                "status": get_label(
                    graph,
                    graph.value(patent_uri, MY0.patentStatus),
                    "",
                ),
                # "vector_id": get_vector_id(graph, patent_uri),
            }
        )

    projects = []
    for project_uri in graph.objects(cv_uri, MY0.hasProject):
        projects.append(
            {
                "name": get_value(graph, project_uri, MY0.projectName),
                "role": get_value(graph, project_uri, MY0.projectRole),
                "start_date": get_value(
                    graph,
                    project_uri,
                    MY0.projectStartDate,
                ),
                "end_date": get_value(
                    graph,
                    project_uri,
                    MY0.projectEndDate,
                ),
                "description": get_value(
                    graph,
                    project_uri,
                    MY0.projectDescription,
                ),
                "creator": get_value(graph, project_uri, MY0.projectCreator),
                "url": get_value(graph, project_uri, MY0.projectURL),
                "is_current": get_boolean(
                    graph,
                    project_uri,
                    MY0.projectIsCurrent,
                ),
                # "vector_id": get_vector_id(graph, project_uri),
            }
        )

    languages = []
    for language_uri in graph.objects(person_uri, MY0.hasSkill):
        if (language_uri, RDF.type, MY0.LanguageSkill) not in graph:
            continue
        languages.append(
            {
                "name": get_value(graph, language_uri, MY0.skillName),
                "proficiency": get_label(
                    graph,
                    graph.value(language_uri, MY0.languageSkillProficiency),
                    "",
                ),
            }
        )

    target = None
    target_uri = graph.value(cv_uri, MY0.hasTarget)
    if target_uri:
        target = {
            "job_title": get_value(graph, target_uri, MY0.targetJobTitle),
            "job_mode": get_label(
                graph,
                graph.value(target_uri, MY0.targetJobType),
                "",
            ),
            "relocate": get_boolean(
                graph,
                target_uri,
                MY0.targetConditionWillRelocate,
            ),
            "travel": get_boolean(
                graph,
                target_uri,
                MY0.targetConditionWillTravel,
            ),
        }

    websites = []
    for website_uri in graph.objects(person_uri, MY0.hasWebsite):
        websites.append(
            {
                "url": get_value(graph, website_uri, MY0.websiteURL),
                "website_type": get_label(
                    graph,
                    graph.value(website_uri, MY0.websiteType),
                    "",
                ),
            }
        )

    instant_messaging = []
    for messaging_uri in graph.objects(person_uri, MY0.hasInstantMessaging):
        instant_messaging.append(
            {
                "name": get_label(
                    graph,
                    graph.value(messaging_uri, MY0.instantMessagingName),
                    "",
                ),
                "username": get_value(
                    graph,
                    messaging_uri,
                    MY0.instantMessagingUsername,
                ),
            }
        )

    honors = []
    for honor_uri in graph.objects(cv_uri, MY0.hasHonorAward):
        honors.append(
            {
                "title": get_value(graph, honor_uri, MY0.honorTitle),
                "issuer": get_value(graph, honor_uri, MY0.honorIssuer),
                "date": get_value(graph, honor_uri, MY0.honorIssuedDate),
            }
        )

    publications = []
    for publication_uri in graph.objects(cv_uri, MY0.hasPublication):
        publications.append(
            {
                "title": get_value(
                    graph,
                    publication_uri,
                    MY0.publicationTitle,
                ),
                "publisher": get_value(
                    graph,
                    publication_uri,
                    MY0.publicationPublisher,
                ),
                "date": get_value(
                    graph,
                    publication_uri,
                    MY0.publicationDate,
                ),
                "description": get_value(
                    graph,
                    publication_uri,
                    MY0.publicationDescription,
                ),
                # "vector_id": get_vector_id(graph, publication_uri),
            }
        )

    references = []
    for reference_uri in graph.objects(cv_uri, MY0.hasReference):
        reference_person_uri = graph.value(reference_uri, MY0.referenceBy)
        references.append(
            {
                "name": get_value(
                    graph,
                    reference_person_uri,
                    MY0.fullName,
                )
                if reference_person_uri
                else "",
                "relation": get_value(
                    graph,
                    reference_uri,
                    MY0.refRelationDescription,
                ),
            }
        )

    other_info = []
    for info_uri in graph.objects(cv_uri, MY0.hasOtherInfo):
        other_info.append(
            {
                "type": get_label(
                    graph,
                    graph.value(info_uri, MY0.otherInfoType),
                    "Misc",
                ),
                "description": get_value(
                    graph,
                    info_uri,
                    MY0.otherInfoDescription,
                ),
            }
        )

    address_uri = graph.value(person_uri, MY0.address)
    skills = get_skills(graph, cv_uri)

    return {
        "name": get_value(graph, person_uri, MY0.fullName, candidate_name),
        "gender": get_label(graph, gender_uri, ""),
        "nationality": nationality,
        "date_of_birth": get_value(graph, person_uri, MY0.dateOfBirth),
        "drivers_licence": get_value(graph, person_uri, MY0.driversLicence),
        "short_description": get_value(
            graph,
            person_uri,
            MY0.personShortDescription,
        ),
        "long_description": get_value(
            graph,
            person_uri,
            MY0.personLongDescription,
        ),
        "email": get_value(graph, person_uri, MY0.email),
        "phone_mobile": get_value(graph, person_uri, MY0.phoneNumberMobile),
        "phone_home": get_value(graph, person_uri, MY0.phoneNumberHome),
        "phone_work": get_value(graph, person_uri, MY0.phoneNumberWork),
        "jobs": jobs,
        "education": education,
        "courses": courses,
        "patents": patents,
        "projects": projects,
        "skills": skills,
        "languages": languages,
        "target": target,
        "address": get_address(graph, address_uri),
        "websites": websites,
        "instant_messaging": instant_messaging,
        "honors": honors,
        "publications": publications,
        "references": references,
        "other_info": other_info,
    }


def get_all_candidate_names():
    query = """
        PREFIX my0: <http://example.com/resume2rdf_ontology.rdf#>
        SELECT DISTINCT ?fullName
        WHERE {
            ?person a my0:Person ;
                    my0:fullName ?fullName .
        }
        ORDER BY LCASE(STR(?fullName))
        """

    names = []
    for row in run_select(query):
        name = row["fullName"]["value"]

        if name not in names:
            names.append(name)
    return names


if __name__ == "__main__":
    data = get_candidate_profile("Kenneth Plum Toft")
    print("\n--- RETRIEVED GRAPH DATA ---")
    print(json.dumps(data, indent=2))
