import sys
import os
import json
import asyncio
import random

# Add the parent directory to Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataset_builder import map_jsonl_to_pydantic

async def test_mapping(num_samples=3):
    input_file = "../datasets/master_resumes.jsonl"
    print(f"Scanning {input_file} for resumes with rare fields (Certifications, Publications, Workshops, Honors)...\n")
    
    try:
        with open(input_file, "r", encoding="utf-8") as infile:
            all_lines = infile.readlines()
            
        if not all_lines:
            print("Error: The file is empty.")
            return

        # Filter the dataset to ONLY include resumes with the fields we want to test
        rare_candidates = []
        for line in all_lines:
            raw = json.loads(line.strip())
            
            has_achievements = bool(raw.get("achievements"))
            has_publications = bool(raw.get("publications"))
            has_workshops = bool(raw.get("workshops"))
            
            # Check if certifications exist and aren't just empty strings
            certs = raw.get("certifications", "")
            has_certs = bool(certs) and certs != "" and certs != '""'
            
            if has_achievements or has_publications or has_workshops or has_certs:
                rare_candidates.append(line)

        print(f"Found {len(rare_candidates)} resumes containing rare fields.")

        if not rare_candidates:
            print("No resumes found matching the criteria. Falling back to all resumes.")
            rare_candidates = all_lines

        actual_samples = min(num_samples, len(rare_candidates))
        sampled_lines = random.sample(rare_candidates, actual_samples)

        for i, line in enumerate(sampled_lines):
            raw_resume = json.loads(line.strip())
            name = raw_resume.get('personal_info', {}).get('name', 'Unknown')
            
            print(f"\n" + "="*80)
            print(f"--- SAMPLE {i+1} | NAME: {name} ---")
            print("="*80 + "\n")
            
            # Print the ORIGINAL raw data first
            print(">>> 1. ORIGINAL RAW JSON <<<")
            print(json.dumps(raw_resume, indent=2))
            print("\n" + "-"*80 + "\n")
            
            # Run the mapping function
            profile = await map_jsonl_to_pydantic(raw_resume)
            
            # Print the NEWLY MAPPED data
            print(">>> 2. MAPPED PYDANTIC PROFILE <<<")
            print(profile.model_dump_json(indent=2))
            print("\n" + "="*80)
            
            # Pause before printing the next one so you can read it
            if i < actual_samples - 1:
                input("\nPress Enter to see the next sample...")
                
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}.")
    except Exception as e:
        print(f"An error occurred during mapping: {e}")

if __name__ == "__main__":
    asyncio.run(test_mapping(num_samples=5))