import subprocess
from designs.texDesign import generateMainDesign1, generateMainDesign2, generateMainDesign3, generateMainDesign4

def generate_and_save_pdf(profile, design_choice, language="en"):
    if profile is None:
        raise ValueError("Profile data is required to generate PDF.")

    if design_choice == 1:
        latex_content = generateMainDesign1(profile, language)
    elif design_choice == 2:
        latex_content = generateMainDesign2(profile, language)
    elif design_choice == 3:
        latex_content = generateMainDesign3(profile, language)
    elif design_choice == 4:
        latex_content = generateMainDesign4(profile, language)
    else:
        raise ValueError("Invalid design choice.")
    
    candidate_name = profile.get("name", "Unknown") if isinstance(profile, dict) else getattr(profile, "name", "Unknown")
    temp_tex = f"temp_{candidate_name.replace(' ', '_')}.tex"
    
    with open(temp_tex, "w", encoding="utf-8") as f:
        f.write(latex_content)

    subprocess.run(["tectonic", temp_tex], check=True)

    return temp_tex.replace(".tex", ".pdf")