from loguru import logger
import re
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD
from SPARQLWrapper import SPARQLWrapper, POST

# 1. Setup Ontological Namespaces
MY0 = Namespace("http://example.com/resume2rdf_ontology.rdf#")
ESCO = Namespace("http://data.europa.eu/esco/model#")

# GraphDB Configuration
GRAPHDB_URL = "http://localhost:7200/repositories/ESCO_Graph/statements"

def sanitize_uri_string(text: str) -> str:
    """Removes special characters to guarantee valid GraphDB IRI."""
    if not text: return "unknown"
    return re.sub(r'[^a-z0-9_]', '', text.lower().strip().replace(" ", "_"))

def create_rdf_graph(candidate_data: dict) -> Graph:
    """Transforms structured CV dict into RDF Triples using Resume2RDF ontology."""
    g = Graph()
    g.bind("my0", MY0)
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
    for idx, job in enumerate(candidate_data.get("experiences", [])):
        work_uri = URIRef(f"http://example.com/data/work_{candidate_slug}_{idx}")
        company_uri = URIRef(f"http://example.com/data/comp_{sanitize_uri_string(job['company_name'])}")
        
        g.add((cv_uri, MY0.hasWorkHistory, work_uri))
        g.add((work_uri, RDF.type, MY0.WorkHistory))
        g.add((work_uri, MY0.jobTitle, Literal(job.get("job_title", ""), datatype=XSD.string)))
        g.add((work_uri, MY0.startDate, Literal(job.get("start_date", ""), datatype=XSD.string)))
        g.add((work_uri, MY0.employedIn, company_uri))
        g.add((company_uri, RDF.type, MY0.Company))
        g.add((company_uri, MY0.orgName, Literal(job.get("company_name", ""), datatype=XSD.string)))
        
        # --- Link Vector Database Reference ---
        if job.get("vector_id"):
            g.add((work_uri, MY0.hasVectorReference, Literal(job["vector_id"], datatype=XSD.string)))

        # --- Link ESCO Skills Directly to This Job ---
        for esco_uri_str in job.get("esco_skill_uris", []):
            esco_skill_uri = URIRef(esco_uri_str)
            g.add((work_uri, MY0.developedSkill, esco_skill_uri))

    # --- Education ---
    for idx, edu in enumerate(candidate_data.get("education", [])):
        edu_uri = URIRef(f"http://example.com/data/edu_{candidate_slug}_{idx}")
        org_uri = URIRef(f"http://example.com/data/uni_{sanitize_uri_string(edu['institution'])}")
        
        g.add((cv_uri, MY0.hasEducation, edu_uri))
        g.add((edu_uri, RDF.type, MY0.Education))
        g.add((edu_uri, MY0.degreeFieldOfStudy, Literal(edu.get("field_of_study", ""), datatype=XSD.string)))
        g.add((edu_uri, MY0.eduStartDate, Literal(edu.get("start_date", ""), datatype=XSD.string)))
        g.add((edu_uri, MY0.eduGradDate, Literal(edu.get("end_date", ""), datatype=XSD.string)))
        g.add((edu_uri, MY0.studiedIn, org_uri))
        g.add((org_uri, RDF.type, MY0.EducationalOrg))
        g.add((org_uri, MY0.orgName, Literal(edu.get("institution", ""), datatype=XSD.string)))

        # --- Link Vector Database Reference ---
        if edu.get("vector_id"):
            g.add((edu_uri, MY0.hasVectorReference, Literal(edu["vector_id"], datatype=XSD.string)))

        # --- Link ESCO Skills Directly to This Education ---
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

    # --- Target Career Preferences ---
    target_data = candidate_data.get("target")
    if target_data:
        target_uri = URIRef(f"http://example.com/data/target_{candidate_slug}")
        g.add((cv_uri, MY0.hasTarget, target_uri))
        g.add((target_uri, RDF.type, MY0.Target))
        g.add((target_uri, MY0.targetJobTitle, Literal(target_data.get("job_title", ""), datatype=XSD.string)))
        g.add((target_uri, MY0.targetConditionWillRelocate, Literal(target_data.get("relocate", False), datatype=XSD.boolean)))
        g.add((target_uri, MY0.targetConditionWillTravel, Literal(target_data.get("travel", False), datatype=XSD.boolean)))
    
    # --- Address ---
    addr = candidate_data.get("address")
    if addr:
        addr_uri = URIRef(f"http://example.com/data/addr_{candidate_slug}")
        g.add((person_uri, MY0.hasAddress, addr_uri))
        g.add((addr_uri, RDF.type, MY0.Address))
        g.add((addr_uri, MY0.city, Literal(addr.get("city", ""))))
        g.add((addr_uri, MY0.country, Literal(addr.get("country", ""))))

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
        g.add((honor_uri, MY0.honorTitle, Literal(honor.get("title", ""))))
        g.add((honor_uri, MY0.honorIssuer, Literal(honor.get("issuer", ""))))
        g.add((honor_uri, MY0.honorDate, Literal(honor.get("date", ""))))

    # --- Publications ---
    for idx, pub in enumerate(candidate_data.get("publications", [])):
        pub_uri = URIRef(f"http://example.com/data/pub_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasPublication, pub_uri))
        g.add((pub_uri, RDF.type, MY0.Publication))
        g.add((pub_uri, MY0.pubTitle, Literal(pub.get("title", ""))))
        g.add((pub_uri, MY0.pubDate, Literal(pub.get("date", ""))))
        
        # --- Link Vector Database Reference ---
        if pub.get("vector_id"):
            g.add((pub_uri, MY0.hasVectorReference, Literal(pub["vector_id"], datatype=XSD.string)))

    # --- References ---
    for idx, ref in enumerate(candidate_data.get("references", [])):
        ref_uri = URIRef(f"http://example.com/data/ref_{candidate_slug}_{idx}")
        g.add((cv_uri, MY0.hasReference, ref_uri))
        g.add((ref_uri, RDF.type, MY0.Reference))
        g.add((ref_uri, MY0.referenceName, Literal(ref.get("name", ""))))
        g.add((ref_uri, MY0.referenceRelation, Literal(ref.get("relation", ""))))
            
    return g

def upload_to_graphdb(graph: Graph):
    """Upserts the graph using Named Graphs for data isolation."""
    cv_uri = next(graph.subjects(RDF.type, MY0.CV), None)
    if not cv_uri: return
        
    named_graph_id = str(cv_uri)
    nt_data = graph.serialize(format="nt")
    
    sparql_query = f"CLEAR GRAPH <{named_graph_id}>; INSERT DATA {{ GRAPH <{named_graph_id}> {{ {nt_data} }} }}"
    
    sparql = SPARQLWrapper(GRAPHDB_URL)
    sparql.setMethod(POST)
    sparql.setQuery(sparql_query)
    sparql.query()