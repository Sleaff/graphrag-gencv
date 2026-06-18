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
    
    SELECT ?jobTitle ?companyName ?startDate ?endDate ?skillName ?degree ?institution ?langName ?eduStart ?eduGrad ?targetTitle ?relocate ?travel ?city ?country ?url ?type ?hTitle ?hIssuer ?hDate ?pTitle ?pDate ?refName ?refRel    WHERE {{
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

        # Target Preferences
        OPTIONAL {{
            ?cv my0:hasTarget ?target .
            ?target my0:targetJobTitle ?targetTitle ;
                    my0:targetConditionWillRelocate ?relocate ;
                    my0:targetConditionWillTravel ?travel .
        }}

        # Address & Websites
        OPTIONAL {{
            ?person my0:hasAddress ?addr .
            ?addr my0:city ?city ; my0:country ?country .
        }}

        OPTIONAL {{
            ?cv my0:hasWebsite ?site .
            ?site my0:websiteURL ?url ; my0:websiteType ?type .
        }}

        # Honors
        OPTIONAL {{
            ?cv my0:hasHonorAward ?honor .
            ?honor my0:honorTitle ?hTitle ;
                   my0:honorIssuer ?hIssuer ;
                   my0:honorDate ?hDate .
        }}

        # Publications
        OPTIONAL {{
            ?cv my0:hasPublication ?pub .
            ?pub my0:pubTitle ?pTitle ;
                 my0:pubDate ?pDate .
        }}

        # References
        OPTIONAL {{
            ?cv my0:hasReference ?ref .
            ?ref my0:referenceName ?refName ;
                 my0:referenceRelation ?refRel .
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
        "languages": set(),
        "target": None,
        "address": None,
        "websites": {},
        "honors": [],
        "publications": [],
        "references": [],
    }
    
    for row in results["results"]["bindings"]:
        if "jobTitle" in row:
            job_key = row["jobTitle"]["value"] + row["companyName"]["value"]
            profile["jobs"][job_key] = {
                "title": row["jobTitle"]["value"],
                "company": row["companyName"]["value"],
                "start": row["startDate"]["value"],
                "end": row.get("endDate", {}).get("value", "Present")
            }
        
        if "degree" in row:
            edu_key = row["degree"]["value"] + row["institution"]["value"]
            profile["education"][edu_key] = {
                "degree": row["degree"]["value"],
                "institution": row["institution"]["value"],
                "start_date": row.get("eduStart", {}).get("value", "N/A"),
                "end_date": row.get("eduGrad", {}).get("value", "N/A")
            }
            
        if "skillName" in row:
            profile["skills"].add(row["skillName"]["value"])
            
        if "langName" in row:
            profile["languages"].add(row["langName"]["value"])

        if "targetTitle" in row and profile["target"] is None:
            profile["target"] = {
                "job_title": row["targetTitle"]["value"],
                "relocate": row["relocate"]["value"].lower() == "true",
                "travel": row["travel"]["value"].lower() == "true"
            }

        if "city" in row:
            profile["address"] = {
                "city": row["city"]["value"],
                "country": row["country"]["value"]
            }

        if "url" in row:
            site_key = row["url"]["value"]
            profile["websites"][site_key] = {
                "url": row["url"]["value"],
                "website_type": row["type"]["value"]
            }
            
        if "hTitle" in row:
            profile["honors"].append({
                "title": row["hTitle"]["value"],
                "issuer": row["hIssuer"]["value"],
                "date": row["hDate"]["value"]
            })
        
        if "pTitle" in row:
            profile["publications"].append({
                "title": row["pTitle"]["value"],
                "date": row["pDate"]["value"]
            })
        
        if "refName" in row:
            profile["references"].append({
                "name": row["refName"]["value"],
                "relation": row["refRel"]["value"]
            })

    # Convert sets/dicts to clean lists for the final profile
    return {
        "name": candidate_name,
        "jobs": list(profile["jobs"].values()),
        "education": list(profile["education"].values()),
        "skills": list(profile["skills"]),
        "languages": list(profile["languages"]),
        "target": profile["target"],
        "address": profile["address"],
        "websites": list(profile["websites"].values()),
        "honors": profile["honors"],
        "publications": profile["publications"],
        "references": profile["references"]
    }

if __name__ == "__main__":
    data = get_candidate_profile("Kenneth Plum Toft")
    print("\n--- RETRIEVED GRAPH DATA ---")
    print(json.dumps(data, indent=2))