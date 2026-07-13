import json

from SPARQLWrapper import JSON, SPARQLWrapper, POST

from settings import GRAPHDB_URL


def get_candidate_profile(candidate_name: str):
    sparql = SPARQLWrapper(GRAPHDB_URL)

    query = f"""
    PREFIX my0: <http://example.com/resume2rdf_ontology.rdf#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT 
        ?gender ?nationality ?dob ?driverLicence ?shortDesc ?longDesc ?email
        ?phoneMobile ?phoneHome ?phoneWork 
        ?imName ?imUsername 
        ?jobTitle ?companyName ?startDate ?endDate ?jobDescription ?careerLevel ?jobType ?jobSkillUri ?jobSkillName ?jobParentLabel
        ?jobCity ?jobCountry
        ?degree ?institution ?eduStart ?eduGrad ?eduDesc 
        ?crsTitle ?crsDesc ?crsUrl ?crsStart ?crsEnd ?crsCert ?crsOrg 
        ?patTitle ?patOffice ?patNum ?patInv ?patUrl ?patDesc ?patDate ?patStatus 
        ?projName ?projRole ?projStart ?projEnd ?projDesc ?projCreator ?projUrl ?projCurrent 
        ?skillUri ?skillName ?parentLabel ?langName ?langProf 
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
        OPTIONAL {{ ?person my0:email ?email . }}
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

            OPTIONAL {{ 
                ?company my0:orgAddress ?jobAddr . 
                OPTIONAL {{ ?jobAddr my0:city ?jobCity . }}
                OPTIONAL {{ ?jobAddr my0:country ?jobCountry . }}
            }}
            
            OPTIONAL {{ 
                ?job my0:hasSkill ?jobSkillUri .
                OPTIONAL {{ ?jobSkillUri my0:skillName ?jobSkillName . }}
                OPTIONAL {{ 
                    ?jobSkillUri skos:broader ?jobParentUri .
                    ?jobParentUri rdfs:label ?jobParentLabel .
                }}
            }}
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
        
        OPTIONAL {{ 
            ?cv my0:hasSkill ?skillUri . 
            OPTIONAL {{ ?skillUri my0:skillName ?skillName . }}
            OPTIONAL {{ 
                ?skillUri skos:broader ?parentUri .
                ?parentUri rdfs:label ?parentLabel .
            }}
        }}
        
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

        OPTIONAL {{
            ?cv my0:hasWebsite ?website .
            ?website my0:websiteURL ?url .
            OPTIONAL {{ ?website my0:websiteType ?type . }}
        }}

        OPTIONAL {{
            ?cv my0:hasTarget ?target .
            ?target my0:targetJobTitle ?targetTitle .
            OPTIONAL {{ ?target my0:targetConditionWillRelocate ?relocate . }}
            OPTIONAL {{ ?target my0:targetConditionWillTravel ?travel . }}
        }}

        OPTIONAL {{
            ?cv my0:hasHonorAward ?honor .
            ?honor my0:honorTitle ?hTitle .
            OPTIONAL {{ ?honor my0:honorIssuer ?hIssuer . }}
            OPTIONAL {{ ?honor my0:honorIssuedDate ?hDate . }}
        }}

        OPTIONAL {{
            ?cv my0:hasPublication ?pub .
            ?pub my0:publicationTitle ?pTitle .
            OPTIONAL {{ ?pub my0:publicationDate ?pDate . }}
            OPTIONAL {{ ?pub my0:publicationDescription ?pDesc . }}
        }}

        OPTIONAL {{
            ?cv my0:hasReference ?ref .
            ?ref my0:referenceName ?refName .
            OPTIONAL {{ ?ref my0:referenceRelation ?refRel . }}
        }}
    }}
    """
    sparql.setMethod(POST)
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
        "email": "",
        "phone_mobile": "",
        "phone_home": "",
        "phone_work": "",
        "jobs": {},
        "education": {},
        "courses": [],
        "patents": [],
        "projects": [],
        "skills": {},
        "languages": {},
        "target": None,
        "address": None,
        "websites": {},
        "instant_messaging": [],
        "honors": [],
        "publications": [],
        "references": [],
        "other_info": [],
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
        if "email" in row and not profile["email"]:
            profile["email"] = row["email"]["value"]
        if "phoneMobile" in row and not profile["phone_mobile"]:
            profile["phone_mobile"] = row["phoneMobile"]["value"]
        if "phoneHome" in row and not profile["phone_home"]:
            profile["phone_home"] = row["phoneHome"]["value"]
        if "phoneWork" in row and not profile["phone_work"]:
            profile["phone_work"] = row["phoneWork"]["value"]

        if "jobTitle" in row:
            start_val = row.get("startDate", {}).get("value", "UnknownStart")
            job_key = row["jobTitle"]["value"] + row["companyName"]["value"] + start_val
            
            if job_key not in profile["jobs"]:
                profile["jobs"][job_key] = {
                    "title": row["jobTitle"]["value"],
                    "company": row["companyName"]["value"],
                    "start": row.get("startDate", {}).get("value", ""),
                    "end": row.get("endDate", {}).get("value", "Present"),
                    "description": row.get("jobDescription", {}).get("value", ""),
                    "career_level": row.get("careerLevel", {}).get("value", ""),
                    "job_type": row.get("jobType", {}).get("value", ""),
                    "address": {
                        "city": row.get("jobCity", {}).get("value", ""),
                        "country": row.get("jobCountry", {}).get("value", "")
                    },
                    "raw_skills": {},
                }
            else:
                # Ensure address updates if missing in first row but present in subsequent rows
                if not profile["jobs"][job_key]["address"]["city"] and "jobCity" in row:
                    profile["jobs"][job_key]["address"]["city"] = row["jobCity"]["value"]
                if not profile["jobs"][job_key]["address"]["country"] and "jobCountry" in row:
                    profile["jobs"][job_key]["address"]["country"] = row["jobCountry"]["value"]
                
            if "jobSkillUri" in row:
                j_uri = row["jobSkillUri"]["value"]
                j_name = row.get("jobSkillName", {}).get("value", j_uri.split("/")[-1])

                if j_name not in profile["jobs"][job_key]["raw_skills"]:
                    profile["jobs"][job_key]["raw_skills"][j_name] = {
                        "name": j_name,
                        "parents": set(),
                    }

                if "jobParentLabel" in row:
                    profile["jobs"][job_key]["raw_skills"][j_name]["parents"].add(
                        row["jobParentLabel"]["value"]
                    )

        # Education
        if "degree" in row:
            edu_key = row["degree"]["value"] + row["institution"]["value"]
            profile["education"][edu_key] = {
                "degree": row["degree"]["value"],
                "institution": row["institution"]["value"],
                "start_date": row.get("eduStart", {}).get("value", "N/A"),
                "end_date": row.get("eduGrad", {}).get("value", "N/A"),
                "description": row.get("eduDesc", {}).get("value", ""),
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
                "has_certification": row.get("crsCert", {}).get("value", "false").lower() == "true",
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
                "status": row.get("patStatus", {}).get("value", ""),
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
                "is_current": row.get("projCurrent", {}).get("value", ""),
            }
            if proj_entry not in profile["projects"]:
                profile["projects"].append(proj_entry)

        # Instant Messaging
        if "imUsername" in row:
            im_entry = {
                "name": row.get("imName", {}).get("value", "IM"),
                "username": row["imUsername"]["value"],
            }
            if im_entry not in profile["instant_messaging"]:
                profile["instant_messaging"].append(im_entry)

        # Other Info
        if "otherDesc" in row:
            other_entry = {
                "type": row.get("otherType", {}).get("value", "Misc"),
                "description": row["otherDesc"]["value"],
            }
            if other_entry not in profile["other_info"]:
                profile["other_info"].append(other_entry)

        # Global Technical Skills
        if "skillUri" in row:
            uri = row["skillUri"]["value"]
            skill_name = row.get("skillName", {}).get("value", uri.split("/")[-1])

            if skill_name not in profile["skills"]:
                profile["skills"][skill_name] = {
                    "name": skill_name,
                    "parents": set(),
                }

            if "parentLabel" in row:
                profile["skills"][skill_name]["parents"].add(
                    row["parentLabel"]["value"]
                )

        # Languages
        if "langName" in row:
            lang_name = row["langName"]["value"]
            profile["languages"][lang_name] = {
                "name": lang_name,
                "proficiency": row.get("langProf", {}).get("value", ""),
            }

        # Target Data
        if "targetTitle" in row and profile["target"] is None:
            profile["target"] = {
                "job_title": row["targetTitle"]["value"],
                "relocate": row["relocate"]["value"].lower() == "true" if "relocate" in row else False,
                "travel": row["travel"]["value"].lower() == "true" if "travel" in row else False,
            }

        # Address Data
        if "city" in row:
            profile["address"] = {
                "city": row["city"]["value"],
                "country": row["country"]["value"],
            }

        # Websites
        if "url" in row:
            site_key = row["url"]["value"]
            profile["websites"][site_key] = {
                "url": row["url"]["value"],
                "website_type": row.get("type", {}).get("value", "Website"),
            }

        # Honors
        if "hTitle" in row:
            honor_entry = {
                "title": row["hTitle"]["value"],
                "issuer": row.get("hIssuer", {}).get("value", ""),
                "date": row.get("hDate", {}).get("value", ""),
            }
            if honor_entry not in profile["honors"]:
                profile["honors"].append(honor_entry)

        # Publications
        if "pTitle" in row:
            pub_entry = {
                "title": row["pTitle"]["value"],
                "date": row.get("pDate", {}).get("value", ""),
                "description": row.get("pDesc", {}).get("value", "")
            }
            if pub_entry not in profile["publications"]:
                profile["publications"].append(pub_entry)

        # References
        if "refName" in row:
            ref_entry = {
                "name": row["refName"]["value"],
                "relation": row.get("refRel", {}).get("value", ""),
            }
            if ref_entry not in profile["references"]:
                profile["references"].append(ref_entry)

    # Convert sets to lists globally
    for skill in profile["skills"].values():
        skill["parents"] = list(skill["parents"])

    # Convert sets to lists for job skills
    for job in profile["jobs"].values():
        for skill in job["raw_skills"].values():
            skill["parents"] = list(skill["parents"])
        job["raw_skills"] = list(job["raw_skills"].values())

    return {
        "name": candidate_name,
        "gender": profile["gender"],
        "nationality": profile["nationality"],
        "date_of_birth": profile["date_of_birth"],
        "drivers_licence": profile["drivers_licence"],
        "short_description": profile["short_description"],
        "long_description": profile["long_description"],
        "email": profile["email"],
        "phone_mobile": profile["phone_mobile"],
        "phone_home": profile["phone_home"],
        "phone_work": profile["phone_work"],
        "jobs": list(profile["jobs"].values()),
        "education": list(profile["education"].values()),
        "courses": profile["courses"],
        "patents": profile["patents"],
        "projects": profile["projects"],
        "skills": list(profile["skills"].values()),
        "languages": list(profile["languages"].values()),
        "target": profile["target"],
        "address": profile["address"],
        "websites": list(profile["websites"].values()),
        "instant_messaging": profile["instant_messaging"],
        "honors": profile["honors"],
        "publications": profile["publications"],
        "references": profile["references"],
        "other_info": profile["other_info"],
    }


def get_all_candidate_names():
    sparql = SPARQLWrapper(GRAPHDB_URL)
    
    query = """
    PREFIX my0: <http://example.com/resume2rdf_ontology.rdf#>
    SELECT ?firstName ?lastName
    WHERE {
        ?person a my0:Person .
        ?person my0:firstName ?firstName .
        OPTIONAL { ?person my0:lastName ?lastName . }
    }
    """
    
    sparql.setQuery(query)
    sparql.setMethod(POST)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    names = []
    for row in results["results"]["bindings"]:
        first = row["firstName"]["value"]
        last = row.get("lastName", {}).get("value", "")
        names.append(f"{first} {last}".strip())
        
    return names

if __name__ == "__main__":
    data = get_candidate_profile("Kenneth Plum Toft")
    print("\n--- RETRIEVED GRAPH DATA ---")
    print(json.dumps(data, indent=2))