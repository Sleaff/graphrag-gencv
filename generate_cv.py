import json
from llm_service import call_llm, ChatMessage
from query_graph import get_candidate_profile

def generate_tailored_cv(candidate_name: str, job_description: str) -> str:
    # 1. Retrieve the verified facts from GraphDB
    profile_data = get_candidate_profile(candidate_name)
    
    # 2. Construct the strict RAG prompt
    prompt = f"""
    You are an expert CV writer. Write a tailored CV for the target Job Description.
    You MUST ONLY use the facts provided in the Candidate Data. Do not invent any experience, roles, or skills.

    Candidate Data:
    {json.dumps(profile_data, indent=2)}

    Job Description:
    {job_description}
    """
    
    messages = [
        ChatMessage(role="system", content="You generate highly tailored CVs based strictly on provided JSON data."),
        ChatMessage(role="user", content=prompt)
    ]
    
    return call_llm(messages)

if __name__ == "__main__":
    target_job = "We are looking for a Software Developer with experience in backend systems, Python, and Docker."
    final_cv = generate_tailored_cv("Kenneth Plum Toft", target_job)
    
    print("\n--- GENERATED TAILORED CV ---")
    print(final_cv)