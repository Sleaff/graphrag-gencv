from SPARQLWrapper import SPARQLWrapper, JSON
import json
from collections import defaultdict

GRAPHDB_URL = "http://localhost:7200/repositories/ESCO_Graph"

def get_candidate_profile(candidate_name: str):
    """Queries GraphDB for the candidate's jobs, companies, dates, and English skill labels."""
    sparql = SPARQLWrapper(GRAPHDB_URL)
    
    query = f"""
    PREFIX my0: <http://example.com/resume2rdf_ontology.rdf#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    
    SELECT ?jobTitle ?companyName ?startDate ?endDate ?skillName ?degree ?institution ?langName ?eduStart ?eduGrad
    WHERE {{
        ?cv a my0:CV ;
            my0:aboutPerson ?person .
        ?person my0:firstName "{candidate_name}" .
        
        # Jobs
        OPTIONAL {{
            ?cv my0:hasWorkHistory ?job .
            ?job my0:jobTitle ?jobTitle ;
                 my0:startDate ?startDate ;
                 my0:employedIn ?company .
            OPTIONAL {{ ?job my0:endDate ?endDate . }}
            ?company my0:orgName ?companyName .
        }}
        
        # Education
        OPTIONAL {{
            ?cv my0:hasEducation ?edu .
            ?edu my0:degreeFieldOfStudy ?degree ;
                 my0:studiedIn ?eduOrg .
            ?eduOrg my0:orgName ?institution .
            
            OPTIONAL {{ ?edu my0:eduStartDate ?eduStart . }}
            OPTIONAL {{ ?edu my0:eduGradDate ?eduGrad . }}
        }}
        
        # Skills
        OPTIONAL {{
            ?cv my0:hasSkill ?skillUri .
            ?skillUri my0:skillName ?skillName .
        }}
        
        # Languages
        OPTIONAL {{
            ?person my0:hasSkill ?lang .
            ?lang a my0:LanguageSkill ;
                  my0:skillName ?langName .
        }}
    }}
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    profile = {
        "name": candidate_name,
        "jobs": {}, 
        "education": {},
        "skills": set(),
        "languages": set()
    }
    
    for row in results["results"]["bindings"]:
        # 1. Map Work History
        if "jobTitle" in row:
            job_key = row["jobTitle"]["value"] + row["companyName"]["value"]
            profile["jobs"][job_key] = {
                "title": row["jobTitle"]["value"],
                "company": row["companyName"]["value"],
                "start": row["startDate"]["value"],
                "end": row.get("endDate", {}).get("value", "Present")
            }
        
        # 2. Map Education
        if "degree" in row:
            edu_key = row["degree"]["value"] + row["institution"]["value"]
            profile["education"][edu_key] = {
                "degree": row["degree"]["value"],
                "institution": row["institution"]["value"],
                "start_date": row.get("eduStart", {}).get("value", "N/A"),
                "end_date": row.get("eduGrad", {}).get("value", "N/A")
            }
            
        # 3. Map Skills
        if "skillName" in row:
            profile["skills"].add(row["skillName"]["value"])
            
        # 4. Map Languages
        if "langName" in row:
            profile["languages"].add(row["langName"]["value"])

    # Convert sets/dicts to clean lists for the final profile
    return {
        "name": candidate_name,
        "jobs": list(profile["jobs"].values()),
        "education": list(profile["education"].values()),
        "skills": list(profile["skills"]),
        "languages": list(profile["languages"])
    }

if __name__ == "__main__":
    data = get_candidate_profile("Kenneth Plum Toft")
    print("\n--- RETRIEVED GRAPH DATA ---")
    print(json.dumps(data, indent=2))