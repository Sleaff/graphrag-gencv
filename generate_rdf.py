from loguru import logger
import re
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD, RDFS
from SPARQLWrapper import SPARQLWrapper, POST

# 1. Setup Ontological Namespaces
MY0 = Namespace("http://example.com/resume2rdf_ontology.rdf#")
MYVALUE0 = Namespace("http://example.com/resume2rdf_value_ontology.rdf#")
ESCO = Namespace("http://data.europa.eu/esco/model#")

# GraphDB Configuration
GRAPHDB_URL = "http://localhost:7200/repositories/ESCO_Graph/statements"

def sanitize_uri_string(text: str) -> str:
    if not text: return "unknown"
    return re.sub(r'[^a-z0-9_]', '', text.lower().strip().replace(" ", "_"))

def create_rdf_graph(candidate_data: dict) -> Graph:
    g = Graph()
    g.bind("my0", MY0)
    g.bind("myvalue0", MYVALUE0)
    g.bind("esco", ESCO)
    
    candidate_slug = sanitize_uri_string(candidate_data.get("name", "Unknown"))
    cv_uri = URIRef(f"http://example.com/data/cv_{candidate_slug}")
    person_uri = URIRef(f"http://example.com/data/person_{candidate_slug}")
    
    # --- Base CV & Person ---
    g.add((cv_uri, RDF.type, MY0.CV))
    g.add((cv_uri, MY0.aboutPerson, person_uri))
    g.add((person_uri, RDF.type, MY0.Person))
    g.add((person_uri, MY0.firstName, Literal(candidate_data.get("name", ""), datatype=XSD.string)))
    
    # --- Work History ---
    for idx, job in enumerate(candidate_data.get("jobs", [])):
        work_uri = URIRef(f"http://example.com/data/work_{candidate_slug}_{idx}")
        company_name = job.get("company", "Unknown") 
        company_uri = URIRef(f"http://example.com/data/comp_{sanitize_uri_string(company_name)}")
        
        g.add((cv_uri, MY0.hasWorkHistory, work_uri))
        g.add((work_uri, RDF.type, MY0.WorkHistory))
        g.add((work_uri, MY0.jobTitle, Literal(job.get("title", ""), datatype=XSD.string)))
        g.add((work_uri, MY0.startDate, Literal(job.get("start", ""), datatype=XSD.string)))
        
        if job.get("end"):
            g.add((work_uri, MY0.endDate, Literal(job.get("end", ""), datatype=XSD.string)))
        if job.get("description"):
            g.add((work_uri, MY0.jobDescription, Literal(job.get("description", ""), datatype=XSD.string)))
            
        g.add((work_uri, MY0.isCurrent, Literal(job.get("is_current", False), datatype=XSD.boolean)))
        g.add((work_uri, MY0.employedIn, company_uri))
        g.add((company_uri, RDF.type, MY0.Company))
        g.add((company_uri, MY0.orgName, Literal(company_name, datatype=XSD.string)))

        # --- Career Level ---
        if job.get("career_level"):
            cl_str = job.get("career_level")
            cl_uri = URIRef(f"http://example.com/data/careerlevel_{sanitize_uri_string(cl_str)}")
            g.add((work_uri, MY0.careerLevel, cl_uri))
            g.add((cl_uri, RDF.type, MYVALUE0.CVCareerLevel))
            g.add((cl_uri, RDFS.label, Literal(cl_str, datatype=XSD.string)))

        # --- Job Type ---
        if job.get("job_type"):
            jt_str = job.get("job_type")
            jt_uri = URIRef(f"http://example.com/data/jobtype_{sanitize_uri_string(jt_str)}")
            g.add((work_uri, MY0.jobType, jt_uri))
            g.add((jt_uri, RDF.type, MYVALUE0.CVEmploymentType))
            g.add((jt_uri, RDFS.label, Literal(jt_str, datatype=XSD.string)))
        
        if job.get("vector_id"):
            g.add((work_uri, MY0.hasVectorReference, Literal(job["vector_id"], datatype=XSD.string)))

        for esco_uri_str in job.get("esco_skill_uris", []):
            esco_skill_uri = URIRef(esco_uri_str)
            g.add((work_uri, MY0.developedSkill, esco_skill_uri))

    # --- Education ---
    for idx, edu in enumerate(candidate_data.get("education", [])):
        edu_uri = URIRef(f"http://example.com/data/edu_{candidate_slug}_{idx}")
        org_uri = URIRef(f"http://example.com/data/uni_{sanitize_uri_string(edu.get('institution', ''))}")
        
        g.add((cv_uri, MY0.hasEducation, edu_uri))
        g.add((edu_uri, RDF.type, MY0.Education))
        g.add((edu_uri, MY0.degreeFieldOfStudy, Literal(edu.get("field_of_study", ""), datatype=XSD.string)))
        g.add((edu_uri, MY0.eduStartDate, Literal(edu.get("start_date", ""), datatype=XSD.string)))
        g.add((edu_uri, MY0.eduGradDate, Literal(edu.get("end_date", ""), datatype=XSD.string)))
        g.add((edu_uri, MY0.studiedIn, org_uri))
        g.add((org_uri, RDF.type, MY0.EducationalOrg))
        g.add((org_uri, MY0.orgName, Literal(edu.get("institution", ""), datatype=XSD.string)))
        
        if edu.get("description"):
            g.add((edu_uri, MY0.eduDescription, Literal(edu.get("description", ""), datatype=XSD.string)))

        if edu.get("degree"):
            deg_str = edu.get("degree")
            deg_uri = URIRef(f"http://example.com/data/degree_{sanitize_uri_string(deg_str)}")
            g.add((edu_uri, MY0.degree, deg_uri))
            g.add((deg_uri, RDF.type, MYVALUE0.EduDegree))
            g.add((deg_uri, RDFS.label, Literal(deg_str, datatype=XSD.string)))

        if edu.get("vector_id"):
            g.add((edu_uri, MY0.hasVectorReference, Literal(edu["vector_id"], datatype=XSD.string)))

        for esco_uri_str in edu.get("esco_skill_uris", []):
            esco_skill_uri = URIRef(esco_uri_str)
            g.add((edu_uri, MY0.developedSkill, esco_skill_uri))

    # --- Technical Skills ---
    for idx, skill_name in enumerate(candidate_data.get("technical_skills", [])):
        skill_uri = URIRef(f"http://example.com/data/skill_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasSkill, skill_uri))
        g.add((skill_uri, RDF.type, MY0.Skill))
        g.add((skill_uri, MY0.skillName, Literal(skill_name, datatype=XSD.string)))

    # --- Language Skills ---
    for idx, lang in enumerate(candidate_data.get("languages", [])):
        lang_uri = URIRef(f"http://example.com/data/lang_{candidate_slug}_{idx}")
        g.add((person_uri, MY0.hasSkill, lang_uri))
        g.add((lang_uri, RDF.type, MY0.LanguageSkill))
        g.add((lang_uri, MY0.skillName, Literal(lang.get("name", ""), datatype=XSD.string)))
        
        if lang.get("proficiency"):
            prof_str = lang.get("proficiency")
            prof_uri = URIRef(f"http://example.com/data/prof_{sanitize_uri_string(prof_str)}")
            
            g.add((lang_uri, MY0.languageSkillProficiency, prof_uri))
            g.add((prof_uri, RDF.type, MYVALUE0.LanguageSkillProficiencyProperty))
            g.add((prof_uri, RDFS.label, Literal(prof_str, datatype=XSD.string)))

    # --- Target Career Preferences ---
    target_data = candidate_data.get("target")
    if target_data:
        target_uri = URIRef(f"http://example.com/data/target_{candidate_slug}")
        g.add((cv_uri, MY0.hasTarget, target_uri))
        g.add((target_uri, RDF.type, MY0.Target))
        g.add((target_uri, MY0.targetJobTitle, Literal(target_data.get("job_title", ""), datatype=XSD.string)))
        g.add((target_uri, MY0.targetConditionWillRelocate, Literal(target_data.get("relocate", False), datatype=XSD.boolean)))
        g.add((target_uri, MY0.targetConditionWillTravel, Literal(target_data.get("travel", False), datatype=XSD.boolean)))
        
        if target_data.get("job_mode"):
            mode_str = target_data.get("job_mode")
            mode_uri = URIRef(f"http://example.com/data/jobtype_{sanitize_uri_string(mode_str)}")
            g.add((target_uri, MY0.targetJobType, mode_uri))
            g.add((mode_uri, RDF.type, MYVALUE0.CVEmploymentType))
            g.add((mode_uri, RDFS.label, Literal(mode_str, datatype=XSD.string)))
    
    # --- Address ---
    addr = candidate_data.get("address")
    if addr:
        addr_uri = URIRef(f"http://example.com/data/addr_{candidate_slug}")
        g.add((person_uri, MY0.hasAddress, addr_uri))
        g.add((addr_uri, RDF.type, MY0.Address))
        g.add((addr_uri, MY0.city, Literal(addr.get("city", ""), datatype=XSD.string)))
        g.add((addr_uri, MY0.country, Literal(addr.get("country", ""), datatype=XSD.string)))
        
        if addr.get("street"):
            g.add((addr_uri, MY0.street, Literal(addr.get("street", ""), datatype=XSD.string)))
        if addr.get("postal_code"):
            g.add((addr_uri, MY0.postalCode, Literal(addr.get("postal_code", ""), datatype=XSD.string)))

    # --- Websites ---
    for idx, site in enumerate(candidate_data.get("websites", [])):
        site_uri = URIRef(f"http://example.com/data/site_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasWebsite, site_uri))
        g.add((site_uri, RDF.type, MY0.Website))
        g.add((site_uri, MY0.websiteURL, Literal(site.get("url", ""))))
        g.add((site_uri, MY0.websiteType, Literal(site.get("website_type", ""))))

    # --- Honors/Awards ---
    for idx, honor in enumerate(candidate_data.get("honors", [])):
        honor_uri = URIRef(f"http://example.com/data/honor_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasHonorAward, honor_uri))
        g.add((honor_uri, RDF.type, MY0.HonorAward))
        g.add((honor_uri, MY0.honortitle, Literal(honor.get("title", ""), datatype=XSD.string)))
        g.add((honor_uri, MY0.honorIssuer, Literal(honor.get("issuer", ""), datatype=XSD.string)))
        g.add((honor_uri, MY0.honorIssuedDate, Literal(honor.get("date", ""), datatype=XSD.string)))

    # --- Publications ---
    for idx, pub in enumerate(candidate_data.get("publications", [])):
        pub_uri = URIRef(f"http://example.com/data/pub_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasPublication, pub_uri))
        g.add((pub_uri, RDF.type, MY0.Publication))
        g.add((pub_uri, MY0.publicationTitle, Literal(pub.get("title", ""), datatype=XSD.string)))
        g.add((pub_uri, MY0.publicationDate, Literal(pub.get("date", ""), datatype=XSD.string)))
        
        if pub.get("publisher"):
             g.add((pub_uri, MY0.publicationPublisher, Literal(pub.get("publisher", ""), datatype=XSD.string)))
        
        if pub.get("vector_id"):
            g.add((pub_uri, MY0.hasVectorReference, Literal(pub["vector_id"], datatype=XSD.string)))

    # --- References ---
    for idx, ref in enumerate(candidate_data.get("references", [])):
        ref_uri = URIRef(f"http://example.com/data/ref_{candidate_slug}_{idx}")
        ref_person_uri = URIRef(f"http://example.com/data/person_ref_{candidate_slug}_{idx}")
        
        g.add((cv_uri, MY0.hasReference, ref_uri))
        g.add((ref_uri, RDF.type, MY0.Reference))
        
        g.add((ref_uri, MY0.referenceBy, ref_person_uri))
        g.add((ref_person_uri, RDF.type, MY0.Person))
        g.add((ref_person_uri, MY0.firstName, Literal(ref.get("name", ""), datatype=XSD.string)))
        
        if ref.get("relation"):
            g.add((ref_uri, MY0.refRelationDescription, Literal(ref.get("relation", ""), datatype=XSD.string)))
            
    return g

def upload_to_graphdb(graph: Graph):
    cv_uri = next(graph.subjects(RDF.type, MY0.CV), None)
    if not cv_uri: return
        
    named_graph_id = str(cv_uri)
    nt_data = graph.serialize(format="nt")
    
    sparql_query = f"CLEAR GRAPH <{named_graph_id}>; INSERT DATA {{ GRAPH <{named_graph_id}> {{ {nt_data} }} }}"
    
    sparql = SPARQLWrapper(GRAPHDB_URL)
    sparql.setMethod(POST)
    sparql.setQuery(sparql_query)
    sparql.query()