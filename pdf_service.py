import subprocess

from designs.texDesign import (
    generateMainDesign1,
    generateMainDesign2,
    generateMainDesign3,
)


def generate_and_save_pdf(profile, design_choice, language="en"):
    if design_choice == 1:
        latex_content = generateMainDesign1(profile, language)
    elif design_choice == 2:
        latex_content = generateMainDesign2(profile, language)
    else:
        latex_content = generateMainDesign3(profile, language)

    temp_tex = f"temp_{profile.name.replace(' ', '_')}.tex"
    with open(temp_tex, "w", encoding="utf-8") as f:
        f.write(latex_content)

    subprocess.run(["pdflatex", "-interaction=nonstopmode", temp_tex], check=True)

    return temp_tex.replace(".tex", ".pdf")
