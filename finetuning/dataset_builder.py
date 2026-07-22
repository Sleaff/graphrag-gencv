import argparse
import asyncio
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from loguru import logger

# Add the parent directory to Python's path so it can find project modules.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cv_to_rdf import (
    Address,
    CandidateProfile,
    Course,
    Education,
    HonorAward,
    Job,
    Language,
    Project,
    Publication,
    Target,
    Website,
    generate_rdf_and_vectors,
)
from generate_cv import tailor_profile_for_job
from query_graph import get_candidate_profile

SYSTEM_INSTRUCTION = (
    "You are a specialized Graph-to-CV generator. Map the Raw Profile to the Target JSON Schema. "
    "Do NOT hallucinate skills or experiences not present in the input graph."
)

DUMMY_JD = (
    "Looking for a skilled professional with strong technical background, "
    "problem-solving skills, and relevant domain experience."
)


def clean_val(value: Any) -> str:
    """Convert null/placeholder values to an empty string."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "unknown", "not provided", "none", "null"}:
        return ""
    return text


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def clean_text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in values:
        text = clean_val(item)
        if text:
            result.append(text)
    return result


def unique_preserving_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def parse_certifications(value: Any) -> list[dict[str, Any]]:
    """Normalize certifications stored as JSON fragments, lists, dicts, or plain text."""
    if isinstance(value, dict):
        return [value]

    if isinstance(value, list):
        result: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                result.append(item)
            else:
                title = clean_val(item)
                if title:
                    result.append({"name": title})
        return result

    raw = clean_val(value)
    if not raw:
        return []

    # First handle a complete JSON value, then the dataset's common
    # comma-separated sequence of JSON objects.
    for candidate in (raw, f"[{raw}]"):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            normalized: list[dict[str, Any]] = []
            for item in parsed:
                if isinstance(item, dict):
                    normalized.append(item)
                else:
                    title = clean_val(item)
                    if title:
                        normalized.append({"name": title})
            return normalized

    # Final fallback for the plain comma-separated certification strings.
    return [
        {"name": title}
        for title in (clean_val(part) for part in raw.split(","))
        if title
    ]


async def map_jsonl_to_pydantic(resume_data: dict[str, Any]) -> CandidateProfile:
    """Map one master_resumes.jsonl record to CandidateProfile safely."""
    if not isinstance(resume_data, dict):
        raise TypeError(f"Resume record must be an object, got {type(resume_data).__name__}")

    personal_info = as_dict(resume_data.get("personal_info"))
    location = as_dict(personal_info.get("location"))

    websites: list[Website] = []
    for key, website_type in (("linkedin", "LinkedIn"), ("github", "GitHub")):
        url = clean_val(personal_info.get(key))
        if url:
            websites.append(Website(url=url, website_type=website_type))

    jobs: list[Job] = []
    for exp in as_list(resume_data.get("experience")):
        if not isinstance(exp, dict):
            continue

        tech_env = as_dict(exp.get("technical_environment"))
        raw_skills = unique_preserving_order(
            clean_text_list(tech_env.get("technologies"))
            + clean_text_list(tech_env.get("tools"))
        )
        responsibilities = clean_text_list(exp.get("responsibilities"))
        dates = as_dict(exp.get("dates"))

        jobs.append(
            Job(
                company=clean_val(exp.get("company")),
                title=clean_val(exp.get("title")),
                start=clean_val(dates.get("start")),
                end=clean_val(dates.get("end")),
                description=" ".join(responsibilities),
                career_level=clean_val(exp.get("level")),
                job_type=clean_val(exp.get("employment_type")),
                raw_skills=raw_skills,
                address=Address(city="", country="", street="", postal_code=""),
                is_current=clean_val(dates.get("end")).lower() == "present",
            )
        )

    education: list[Education] = []
    for edu in as_list(resume_data.get("education")):
        if not isinstance(edu, dict):
            continue

        degree_info = as_dict(edu.get("degree"))
        institution_info = as_dict(edu.get("institution"))
        dates = as_dict(edu.get("dates"))
        achievements = as_dict(edu.get("achievements"))
        coursework = clean_text_list(achievements.get("relevant_coursework"))

        education.append(
            Education(
                degree=clean_val(degree_info.get("level")),
                institution=clean_val(institution_info.get("name")),
                start_date=clean_val(dates.get("start")),
                end_date=clean_val(dates.get("expected_graduation")),
                field_of_study=clean_val(degree_info.get("field")),
                description=", ".join(coursework),
            )
        )

    projects: list[Project] = []
    for project in as_list(resume_data.get("projects")):
        if not isinstance(project, dict):
            continue
        name = clean_val(project.get("name"))
        if not name:
            continue

        description_parts = [
            clean_val(project.get("description")),
            clean_val(project.get("impact")),
        ]
        description = " ".join(part for part in description_parts if part)

        projects.append(
            Project(
                name=name,
                role=clean_val(project.get("role")),
                start_date=clean_val(project.get("start_date")),
                end_date=clean_val(project.get("end_date")),
                description=description,
                url=clean_val(project.get("url")),
                creator="",
                is_current=False,
            )
        )

    technical_skills: list[str] = []
    languages: list[Language] = []
    skills_data = as_dict(resume_data.get("skills"))
    technical = as_dict(skills_data.get("technical"))

    # Iterate every category rather than a fixed allow-list. The dataset also
    # contains project_management, automation, software_tools, testing, etc.
    for entries in technical.values():
        for skill in as_list(entries):
            if isinstance(skill, dict):
                name = clean_val(skill.get("name"))
            else:
                name = clean_val(skill)
            if name:
                technical_skills.append(name)

    for language in as_list(skills_data.get("languages")):
        if not isinstance(language, dict):
            continue
        name = clean_val(language.get("name"))
        if name:
            languages.append(
                Language(name=name, proficiency=clean_val(language.get("level")))
            )

    honors: list[HonorAward] = []
    for achievement in as_list(resume_data.get("achievements")):
        if isinstance(achievement, dict):
            title = clean_val(achievement.get("title") or achievement.get("name"))
            issuer = clean_val(achievement.get("issuer"))
            date = clean_val(achievement.get("date"))
        else:
            title = clean_val(achievement)
            issuer = ""
            date = ""
        if title:
            honors.append(HonorAward(title=title, issuer=issuer, date=date))

    publications: list[Publication] = []
    for publication in as_list(resume_data.get("publications")):
        if not isinstance(publication, dict):
            continue
        title = clean_val(publication.get("title"))
        if title:
            publications.append(
                Publication(
                    title=title,
                    publisher=(
                        clean_val(publication.get("conference"))
                        or clean_val(publication.get("publisher"))
                    ),
                    date=clean_val(publication.get("date")),
                    description=clean_val(publication.get("description")),
                )
            )

    courses: list[Course] = []
    for workshop in as_list(resume_data.get("workshops")):
        if not isinstance(workshop, dict):
            continue
        title = clean_val(workshop.get("name") or workshop.get("title"))
        if title:
            courses.append(
                Course(
                    title=title,
                    organized_by=clean_val(workshop.get("issuer")),
                    start_date=clean_val(workshop.get("date")),
                    description=clean_val(workshop.get("description")),
                    url=clean_val(workshop.get("url")),
                    finish_date="",
                    has_certification=False,
                )
            )

    for certification in parse_certifications(resume_data.get("certifications")):
        title = clean_val(certification.get("name") or certification.get("title"))
        if title:
            courses.append(
                Course(
                    title=title,
                    organized_by=clean_val(certification.get("issuer")),
                    start_date=clean_val(certification.get("date")),
                    description=(
                        clean_val(certification.get("description"))
                        or clean_val(certification.get("details"))
                    ),
                    url=clean_val(certification.get("url")),
                    finish_date="",
                    has_certification=True,
                )
            )

    return CandidateProfile(
        name=clean_val(personal_info.get("name")),
        gender="",
        nationality="",
        date_of_birth="",
        drivers_licence="",
        short_description="",
        long_description=clean_val(personal_info.get("summary")),
        email=clean_val(personal_info.get("email")),
        phone_mobile=clean_val(personal_info.get("phone")),
        phone_home="",
        phone_work="",
        address=Address(
            city=clean_val(location.get("city")),
            country=clean_val(location.get("country")),
            street="",
            postal_code="",
        ),
        jobs=jobs,
        education=education,
        courses=courses,
        patents=[],
        projects=projects,
        technical_skills=unique_preserving_order(technical_skills),
        languages=languages,
        target=Target(job_title="", job_mode="", relocate=False, travel=False),
        websites=websites,
        instant_messaging=[],
        honors=honors,
        publications=publications,
        references=[],
        other_info=[],
    )


def make_json_safe(value: Any) -> Any:
    """Recursively convert supported Python containers to JSON-safe values.

    Graph query helpers may return sets for fields such as ESCO parent categories.
    Sets are converted to deterministically sorted lists so generated JSONL files are
    valid and reproducible across runs.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    if isinstance(value, (set, frozenset)):
        normalized = [make_json_safe(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        )

    # Keep this strict so new unsupported graph values fail close to their source
    # instead of being silently converted into misleading strings.
    raise TypeError(f"Unsupported value for JSON serialization: {type(value).__name__}")


def parse_json_object(value: Any, label: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return make_json_safe(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty JSON object")

    text = value.strip()
    if text.startswith("```json"):
        text = text[len("```json") :].split("```", 1)[0].strip()
    elif text.startswith("```"):
        text = text[3:].split("```", 1)[0].strip()

    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise TypeError(f"{label} must decode to an object, got {type(parsed).__name__}")
    return make_json_safe(parsed)


def graph_context_has_content(context: dict[str, Any]) -> bool:
    scalar_fields = ("name", "short_description", "long_description", "email", "phone_mobile")
    list_fields = ("jobs", "education", "projects", "skills", "technical_skills", "courses")
    return any(clean_val(context.get(field)) for field in scalar_fields) or any(
        bool(context.get(field)) for field in list_fields
    )


async def fetch_graph_context(candidate_name: str, attempts: int = 3) -> dict[str, Any]:
    last_context: dict[str, Any] = {}
    for attempt in range(1, attempts + 1):
        raw_context = get_candidate_profile(candidate_name)
        last_context = parse_json_object(raw_context, "Graph context")
        if graph_context_has_content(last_context):
            return last_context
        if attempt < attempts:
            await asyncio.sleep(0.25 * attempt)
    raise RuntimeError(
        f"Graph lookup for {candidate_name!r} returned an empty profile after {attempts} attempts"
    )


async def build_training_dataset(
    input_file: str = "../datasets/master_resumes.jsonl",
    output_file: str = "finetune_data.jsonl",
    max_samples: Optional[int] = None,
    seed: int = 42,
) -> None:
    logger.info("Loading local dataset from {}...", input_file)
    rng = random.Random(seed)
    counts: Counter[str] = Counter()
    seen_graph_names: Counter[str] = Counter()

    input_path = Path(input_file)
    output_path = Path(output_file)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")

    with input_path.open("r", encoding="utf-8") as infile, temp_path.open(
        "w", encoding="utf-8"
    ) as outfile:
        for line_number, line in enumerate(infile, start=1):
            if max_samples is not None and counts["read"] >= max_samples:
                break
            if not line.strip():
                continue

            counts["read"] += 1
            try:
                raw_resume = json.loads(line)
                profile = await map_jsonl_to_pydantic(raw_resume)

                display_name = profile.name
                base_graph_name = display_name or f"Anonymous_{line_number - 1}"
                duplicate_number = seen_graph_names[base_graph_name]
                seen_graph_names[base_graph_name] += 1
                graph_name = (
                    base_graph_name
                    if duplicate_number == 0
                    else f"{base_graph_name}_{line_number - 1}"
                )

                # The graph/vector layers currently use the candidate name as their ID.
                # Give every record a non-empty unique internal name to prevent overwrites.
                profile.name = graph_name
                logger.info(
                    "Processing record {} as graph candidate {!r}",
                    line_number,
                    graph_name,
                )

                await generate_rdf_and_vectors(profile)
                graph_context = await fetch_graph_context(graph_name)

                # Do not teach the model synthetic storage identifiers as a person's name.
                graph_context["name"] = display_name

                assigned_max_pages = rng.choice([1, 2, 3, None])
                page_limit_tag = (
                    str(assigned_max_pages) if assigned_max_pages is not None else "None"
                )

                tailored = tailor_profile_for_job(
                    DUMMY_JD, graph_context, assigned_max_pages
                )
                target_json = parse_json_object(tailored, "Tailored CV")

                training_pair = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {
                            "role": "user",
                            "content": (
                                f"Target Length: <max_pages: {page_limit_tag}>\n\n"
                                f"Job Description:\n{DUMMY_JD}\n\n"
                                "Raw Profile:\n"
                                + json.dumps(graph_context, ensure_ascii=False)
                            ),
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(target_json, ensure_ascii=False),
                        },
                    ]
                }
                outfile.write(json.dumps(training_pair, ensure_ascii=False) + "\n")
                outfile.flush()
                counts["written"] += 1

            except Exception:
                counts["skipped"] += 1
                logger.exception(
                    "Skipping input line {} after an unexpected error", line_number
                )

    if counts["written"] == 0:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"No training rows were generated; {counts['skipped']} records failed"
        )

    temp_path.replace(output_path)
    logger.success(
        "Dataset generated: {} rows written, {} skipped, {} read. Saved to {}",
        counts["written"],
        counts["skipped"],
        counts["read"],
        output_path,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build graph-to-CV fine-tuning data")
    parser.add_argument(
        "--input",
        default="../datasets/master_resumes.jsonl",
        help="Input JSONL file",
    )
    parser.add_argument(
        "--output",
        default="finetune_data.jsonl",
        help="Output JSONL file",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum input records to read; omit to process the complete file",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        build_training_dataset(
            input_file=args.input,
            output_file=args.output,
            max_samples=args.max_samples,
            seed=args.seed,
        )
    )