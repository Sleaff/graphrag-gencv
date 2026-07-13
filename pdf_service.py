import re
import subprocess
import uuid

from designs.texDesign import generateDesign1, generateDesign2, generateDesign3, generateDesign4


def generate_and_save_pdf(profile, design_choice, language="en"):
    if profile is None:
        raise ValueError("Profile data is required to generate PDF.")

    if design_choice == 1:
        latex_content = generateDesign1(profile, language)
    elif design_choice == 2:
        latex_content = generateDesign2(profile, language)
    elif design_choice == 3:
        latex_content = generateDesign3(profile, language)
    elif design_choice == 4:
        latex_content = generateDesign4(profile, language)
    else:
        raise ValueError("Invalid design choice.")

    candidate_name = (
        profile.get("name", "Unknown")
        if isinstance(profile, dict)
        else getattr(profile, "name", "Unknown")
    )
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", candidate_name).strip("_") or "Unknown"
    unique_id = uuid.uuid4().hex
    temp_tex = f"temp_{safe_name}_{unique_id}.tex"

    with open(temp_tex, "w", encoding="utf-8") as file:
        file.write(latex_content)

    subprocess.run(["tectonic", temp_tex], check=True)
    return temp_tex.replace(".tex", ".pdf")
