from SPARQLWrapper import SPARQLWrapper, JSON
import json
from collections import defaultdict

GRAPHDB_URL = "http://localhost:7200/repositories/ResumeGraph"

def get_candidate_profile(candidate_name: str):
    sparql = SPARQLWrapper(GRAPHDB_URL)
    
    query = f"""
    PREFIX my0: <http://example.com/resume2rdf_ontology.rdf#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT 
        ?gender ?nationality ?dob ?driverLicence ?shortDesc ?longDesc 
        ?phoneMobile ?phoneHome ?phoneWork 
        ?imName ?imUsername 
        ?jobTitle ?companyName ?startDate ?endDate ?jobDescription ?careerLevel ?jobType 
        ?degree ?institution ?eduStart ?eduGrad ?eduDesc 
        ?crsTitle ?crsDesc ?crsUrl ?crsStart ?crsEnd ?crsCert ?crsOrg 
        ?patTitle ?patOffice ?patNum ?patInv ?patUrl ?patDesc ?patDate ?patStatus 
        ?projName ?projRole ?projStart ?projEnd ?projDesc ?projCreator ?projUrl ?projCurrent 
        ?skillName ?langName ?langProf 
        ?targetTitle ?relocate ?travel ?city ?country ?url ?type 
        ?hTitle ?hIssuer ?hDate ?pTitle ?pDate ?pDesc ?refName ?refRel 
        ?otherType ?otherDesc
    WHERE {{
        ?cv a my0:CV ;
            my0:aboutPerson ?person .
        ?person my0:firstName "{candidate_name}" .
        
        # Person Details
        OPTIONAL {{ ?person my0:gender ?gObj . ?gObj rdfs:label ?gender . }}
        OPTIONAL {{ ?person my0:hasNationality ?nat . BIND(REPLACE(STR(?nat), ".*#", "") AS ?nationality) }}
        OPTIONAL {{ ?person my0:dateOfBirth ?dob . }}
        OPTIONAL {{ ?person my0:driversLicence ?driverLicence . }}
        OPTIONAL {{ ?person my0:personShortDescription ?shortDesc . }}
        OPTIONAL {{ ?person my0:personLongDescription ?longDesc . }}
        OPTIONAL {{ ?person my0:phoneNumberMobile ?phoneMobile . }}
        OPTIONAL {{ ?person my0:phoneNumberHome ?phoneHome . }}
        OPTIONAL {{ ?person my0:phoneNumberWork ?phoneWork . }}

        OPTIONAL {{
            ?person my0:hasInstantMessaging ?im .
            ?im my0:instantMessagingUsername ?imUsername .
            OPTIONAL {{ ?im my0:instantMessagingName ?imObj . ?imObj rdfs:label ?imName . }}
        }}

        OPTIONAL {{
            ?cv my0:hasWorkHistory ?job .
            ?job my0:jobTitle ?jobTitle ; my0:startDate ?startDate ; my0:employedIn ?company .
            ?company my0:orgName ?companyName .
            OPTIONAL {{ ?job my0:endDate ?endDate . }}
            OPTIONAL {{ ?job my0:jobDescription ?jobDescription . }}
            OPTIONAL {{ ?job my0:careerLevel ?clObj . ?clObj rdfs:label ?careerLevel . }}
            OPTIONAL {{ ?job my0:jobType ?jtObj . ?jtObj rdfs:label ?jobType . }}
        }}
        
        OPTIONAL {{
            ?cv my0:hasEducation ?edu .
            ?edu my0:degreeFieldOfStudy ?degree ; my0:studiedIn ?eduOrg .
            ?eduOrg my0:orgName ?institution .
            OPTIONAL {{ ?edu my0:eduStartDate ?eduStart . }}
            OPTIONAL {{ ?edu my0:eduGradDate ?eduGrad . }}
            OPTIONAL {{ ?edu my0:eduDescription ?eduDesc . }}
        }}

        OPTIONAL {{
            ?cv my0:hasCourse ?crs .
            ?crs my0:courseTitle ?crsTitle .
            OPTIONAL {{ ?crs my0:courseDescription ?crsDesc . }}
            OPTIONAL {{ ?crs my0:courseURL ?crsUrl . }}
            OPTIONAL {{ ?crs my0:courseStartDate ?crsStart . }}
            OPTIONAL {{ ?crs my0:courseFinishDate ?crsEnd . }}
            OPTIONAL {{ ?crs my0:hasCertification ?crsCert . }}
            OPTIONAL {{ ?crs my0:organizedBy ?crsOrgObj . ?crsOrgObj my0:orgName ?crsOrg . }}
        }}

        OPTIONAL {{
            ?cv my0:hasPatent ?pat .
            ?pat my0:patentTitle ?patTitle .
            OPTIONAL {{ ?pat my0:patentOffice ?patOffice . }}
            OPTIONAL {{ ?pat my0:patentNumber ?patNum . }}
            OPTIONAL {{ ?pat my0:patentInventor ?patInv . }}
            OPTIONAL {{ ?pat my0:patentURL ?patUrl . }}
            OPTIONAL {{ ?pat my0:patentDescription ?patDesc . }}
            OPTIONAL {{ ?pat my0:patentIssuedDate ?patDate . }}
            OPTIONAL {{ ?pat my0:patentStatus ?patObj . ?patObj rdfs:label ?patStatus . }}
        }}

        OPTIONAL {{
            ?cv my0:hasProject ?proj .
            ?proj my0:projectName ?projName .
            OPTIONAL {{ ?proj my0:projectRole ?projRole . }}
            OPTIONAL {{ ?proj my0:projectStartDate ?projStart . }}
            OPTIONAL {{ ?proj my0:projectEndDate ?projEnd . }}
            OPTIONAL {{ ?proj my0:projectDescription ?projDesc . }}
            OPTIONAL {{ ?proj my0:projectCreator ?projCreator . }}
            OPTIONAL {{ ?proj my0:projectURL ?projUrl . }}
            OPTIONAL {{ ?proj my0:projectIsCurrent ?projCurrent . }}
        }}
        
        OPTIONAL {{ ?cv my0:hasSkill ?skillUri . ?skillUri my0:skillName ?skillName . }}
        OPTIONAL {{
            ?person my0:hasSkill ?lang . ?lang a my0:LanguageSkill ; my0:skillName ?langName .
            OPTIONAL {{ ?lang my0:languageSkillProficiency ?profObj . ?profObj rdfs:label ?langProf . }}
        }}

        OPTIONAL {{
            ?cv my0:hasOtherInfo ?other .
            ?other my0:otherInfoDescription ?otherDesc .
            OPTIONAL {{ ?other my0:otherInfoType ?otherObj . ?otherObj rdfs:label ?otherType . }}
        }}

        OPTIONAL {{ ?person my0:hasAddress ?addr . ?addr my0:city ?city ; my0:country ?country . }}
    }}
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    profile = {
        "name": candidate_name, 
        "gender": "", 
        "nationality": "", 
        "date_of_birth": "", 
        "drivers_licence": "", 
        "short_description": "", 
        "long_description": "",
        "phone_mobile": "", 
        "phone_home": "", 
        "phone_work": "",
        "jobs": {}, 
        "education": {}, 
        "courses": [], 
        "patents": [], 
        "projects": [], 
        "skills": set(), 
        "languages": {},
        "target": None, 
        "address": None, 
        "websites": {}, 
        "instant_messaging": [], 
        "honors": [], 
        "publications": [], 
        "references": [], 
        "other_info": []
    }
    
    for row in results["results"]["bindings"]:
        # Scalars (Person details)
        if "gender" in row and not profile["gender"]:
            profile["gender"] = row["gender"]["value"]
        if "nationality" in row and not profile["nationality"]:
            profile["nationality"] = row["nationality"]["value"]
        if "dob" in row and not profile["date_of_birth"]:
            profile["date_of_birth"] = row["dob"]["value"]
        if "driverLicence" in row and not profile["drivers_licence"]:
            profile["drivers_licence"] = row["driverLicence"]["value"]
        if "shortDesc" in row and not profile["short_description"]:
            profile["short_description"] = row["shortDesc"]["value"]
        if "longDesc" in row and not profile["long_description"]:
            profile["long_description"] = row["longDesc"]["value"]
        if "phoneMobile" in row and not profile["phone_mobile"]:
            profile["phone_mobile"] = row["phoneMobile"]["value"]
        if "phoneHome" in row and not profile["phone_home"]:
            profile["phone_home"] = row["phoneHome"]["value"]
        if "phoneWork" in row and not profile["phone_work"]:
            profile["phone_work"] = row["phoneWork"]["value"]

        # Jobs
        if "jobTitle" in row:
            job_key = row["jobTitle"]["value"] + row["companyName"]["value"]
            profile["jobs"][job_key] = {
                "title": row["jobTitle"]["value"],
                "company": row["companyName"]["value"],
                "start": row["startDate"]["value"],
                "end": row.get("endDate", {}).get("value", "Present"),
                "description": row.get("jobDescription", {}).get("value", ""),
                "career_level": row.get("careerLevel", {}).get("value", ""),
                "job_type": row.get("jobType", {}).get("value", "")
            }
        
        # Education
        if "degree" in row:
            edu_key = row["degree"]["value"] + row["institution"]["value"]
            profile["education"][edu_key] = {
                "degree": row["degree"]["value"],
                "institution": row["institution"]["value"],
                "start_date": row.get("eduStart", {}).get("value", "N/A"),
                "end_date": row.get("eduGrad", {}).get("value", "N/A"),
                "description": row.get("eduDesc", {}).get("value", "")
            }

        # Courses
        if "crsTitle" in row:
            crs_entry = {
                "title": row["crsTitle"]["value"],
                "description": row.get("crsDesc", {}).get("value", ""),
                "url": row.get("crsUrl", {}).get("value", ""),
                "start_date": row.get("crsStart", {}).get("value", ""),
                "finish_date": row.get("crsEnd", {}).get("value", ""),
                "organized_by": row.get("crsOrg", {}).get("value", ""),
                "has_certification": row.get("crsCert", {}).get("value", "false").lower() == "true"
            }
            if crs_entry not in profile["courses"]:
                profile["courses"].append(crs_entry)

        # Patents
        if "patTitle" in row:
            pat_entry = {
                "title": row["patTitle"]["value"],
                "office": row.get("patOffice", {}).get("value", ""),
                "number": row.get("patNum", {}).get("value", ""),
                "inventor": row.get("patInv", {}).get("value", ""),
                "url": row.get("patUrl", {}).get("value", ""),
                "description": row.get("patDesc", {}).get("value", ""),
                "issued_date": row.get("patDate", {}).get("value", ""),
                "status": row.get("patStatus", {}).get("value", "")
            }
            if pat_entry not in profile["patents"]:
                profile["patents"].append(pat_entry)

        # Projects
        if "projName" in row:
            proj_entry = {
                "name": row["projName"]["value"],
                "role": row.get("projRole", {}).get("value", ""),
                "start_date": row.get("projStart", {}).get("value", ""),
                "end_date": row.get("projEnd", {}).get("value", ""),
                "description": row.get("projDesc", {}).get("value", ""),
                "creator": row.get("projCreator", {}).get("value", ""),
                "url": row.get("projUrl", {}).get("value", ""),
                "is_current": row.get("projCurrent", {}).get("value", "false").lower() == "true"
            }
            if proj_entry not in profile["projects"]:
                profile["projects"].append(proj_entry)

        # Instant Messaging
        if "imUsername" in row:
            im_entry = {
                "name": row.get("imName", {}).get("value", "IM"),
                "username": row["imUsername"]["value"]
            }
            if im_entry not in profile["instant_messaging"]:
                profile["instant_messaging"].append(im_entry)

        # Other Info
        if "otherDesc" in row:
            other_entry = {
                "type": row.get("otherType", {}).get("value", "Misc"),
                "description": row["otherDesc"]["value"]
            }
            if other_entry not in profile["other_info"]:
                profile["other_info"].append(other_entry)
            
        # Skills & Languages
        if "skillName" in row:
            profile["skills"].add(row["skillName"]["value"])
            
        if "langName" in row:
            lang_name = row["langName"]["value"]
            profile["languages"][lang_name] = {
                "name": lang_name,
                "proficiency": row.get("langProf", {}).get("value", "")
            }

        # Target Data
        if "targetTitle" in row and profile["target"] is None:
            profile["target"] = {
                "job_title": row["targetTitle"]["value"],
                "relocate": row["relocate"]["value"].lower() == "true",
                "travel": row["travel"]["value"].lower() == "true"
            }

        # Address Data
        if "city" in row:
            profile["address"] = {
                "city": row["city"]["value"],
                "country": row["country"]["value"]
            }

        # Websites
        if "url" in row:
            site_key = row["url"]["value"]
            profile["websites"][site_key] = {
                "url": row["url"]["value"],
                "website_type": row["type"]["value"]
            }
            
        # Honors
        if "hTitle" in row:
            honor_entry = {
                "title": row["hTitle"]["value"],
                "issuer": row["hIssuer"]["value"],
                "date": row["hDate"]["value"]
            }
            if honor_entry not in profile["honors"]:
                profile["honors"].append(honor_entry)
        
        # Publications
        if "pTitle" in row:
            pub_entry = {
                "title": row["pTitle"]["value"],
                "date": row["pDate"]["value"]
            }
            if pub_entry not in profile["publications"]:
                profile["publications"].append(pub_entry)
        
        # References
        if "refName" in row:
            ref_entry = {
                "name": row["refName"]["value"],
                "relation": row.get("refRel", {}).get("value", "")
            }
            if ref_entry not in profile["references"]:
                profile["references"].append(ref_entry)

    # Convert sets and dict mappings back to lists
    return {
        "name": candidate_name,
        "gender": profile["gender"], 
        "nationality": profile["nationality"], 
        "date_of_birth": profile["date_of_birth"], 
        "drivers_licence": profile["drivers_licence"], 
        "short_description": profile["short_description"], 
        "long_description": profile["long_description"],
        "phone_mobile": profile["phone_mobile"], 
        "phone_home": profile["phone_home"], 
        "phone_work": profile["phone_work"],
        "jobs": list(profile["jobs"].values()), 
        "education": list(profile["education"].values()),
        "courses": profile["courses"], 
        "patents": profile["patents"], 
        "projects": profile["projects"],
        "skills": list(profile["skills"]), 
        "languages": list(profile["languages"].values()), 
        "target": profile["target"],
        "address": profile["address"], 
        "websites": list(profile["websites"].values()), 
        "instant_messaging": profile["instant_messaging"],
        "honors": profile["honors"], 
        "publications": profile["publications"], 
        "references": profile["references"], 
        "other_info": profile["other_info"]
    }

if __name__ == "__main__":
    data = get_candidate_profile("Kenneth Plum Toft")
    print("\n--- RETRIEVED GRAPH DATA ---")
    print(json.dumps(data, indent=2))