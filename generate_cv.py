import json

from loguru import logger

from llm_service import ChatMessage, call_llm
from query_graph import get_candidate_profile


def generate_tailored_cv(job_description: str, profile_data: dict) -> str:

    prompt = f"""
    You are an expert CV writer. Write a tailored CV for the target Job Description.
    You MUST ONLY use the facts provided in the Candidate Data below. Do not invent any experience, roles, or skills.

    Candidate Data:
    {json.dumps(profile_data, indent=2)}

    Job Description:
    {job_description}
    """

    messages = [
        ChatMessage(
            role="system",
            content="You generate highly tailored CVs based strictly on provided JSON data.",
        ),
        ChatMessage(role="user", content=prompt),
    ]

    result = call_llm(messages)
    logger.success("Tailored CV generated successfully.")
    return result


if __name__ == "__main__":
    target_job = "We are looking for a Software Developer with experience in backend systems, Python, and Docker."
    # Assuming you have a way to retrieve the verified candidate profile data
    profile_data = get_candidate_profile("Kenneth Plum Toft")
    final_cv = generate_tailored_cv(target_job, profile_data)

    print("\n--- GENERATED TAILORED CV ---")
    print(final_cv)
