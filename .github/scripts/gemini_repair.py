import os
import json
import glob
import re
import sys
from google import genai
from google.genai import types

def gather_all_failed_allure_contexts(results_dir="report/allure-results"):
    """
    Scans the Allure results directory and groups unique failures 
    by their respective target Page Object files.
    """
    if not os.path.exists(results_dir):
        print(f"❌ Allure results directory not found at: {results_dir}")
        return {}

    # Map of target_page_path -> list of error logs/traces
    failed_batches = {}
    result_files = glob.glob(os.path.join(results_dir, "*-result.json"))
    
    for file_path in result_files:
        with open(file_path, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        
        if test_data.get("status") in ["failed", "broken"]:
            status_details = test_data.get("statusDetails", {})
            error_log = status_details.get("message", "") + "\n" + status_details.get("trace", "")
            
            # Find the accompanying test specification name
            spec_file = "Unknown"
            for label in test_data.get("labels",):
                if label.get("name") == "suite":
                    spec_file = label.get("value", "")

            # Trace which Page Object file under /pages/ crashed
            page_match = re.search(r"pages/[\w-]+\.ts", error_log)
            if page_match:
                target_page_path = page_match.group(0)
            else:
                # Fallback Strategy: Infer Page name from spec name
                base_name = os.path.basename(spec_file).replace(".spec.ts", "")
                target_page_path = f"pages/{base_name}.page.ts"

            if os.path.exists(target_page_path):
                if target_page_path not in failed_batches:
                    failed_batches[target_page_path] = []
                failed_batches[target_page_path].append(error_log)
                
    return failed_batches

def run_batch_allure_repair():
    failed_batches = gather_all_failed_allure_contexts()
    
    if not failed_batches:
        print("✅ No test failures found in Allure results. Pipeline is healthy.")
        sys.exit(2) # Exit code 2 tells GHA: Nothing to do, skip re-testing

    # Initialize the standard, cost-effective GenAI Client
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    system_instruction = (
        "You are an expert Playwright automation agent. Your sole purpose is fixing flaky selectors "
        "and synchronization issues within Page Object files inside the /pages directory. "
        "You must respond ONLY with the raw updated TypeScript code. Do not include markdown wraps or ``` blocks."
    )

    any_file_modified = False

    # Iterate through every unique Page Object file that experienced a failure
    for target_page_path, error_logs in failed_batches.items():
        print(f"\n🎯 Processing failures targeting: {target_page_path}")
        print(f"   Collected {len(error_logs)} failure instances for this page.")

        with open(target_page_path, "r", encoding="utf-8") as f:
            original_page_code = f.read()

        # Combine all separate error logs targeting this file into a single contextual prompt
        combined_errors_context = "\n--- Next Failure Instance ---\n".join(error_logs)

        prompt = f"""
        The test suite encountered element interaction errors pointing to this Page Object class.
        Review all failure variations below and optimize the class methods/selectors to fix them all.

        ALLURE COMBINED FAILURE VARIATIONS:
        {combined_errors_context}

        CURRENT PAGE OBJECT CODE:
        {original_page_code}

        BOUNDED RULES:
        1. Look for properties causing timeouts in the constructor (e.g., CSS ids like '#lastName').
        2. Optimize changing or dynamic #ids using modern user-facing Playwright locator frameworks.
        3. NEVER add raw 'page.waitForTimeout()' delays.
        4. Provide the COMPLETE updated code for {target_page_path}.
        """

        print("🤖 Dispatching batch repair to gemini-3.8-flash...")
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )

        cleaned_code = re.sub(r'^```ts\s*|^```typescript\s*|^```\s*|```$', '', response.text.strip(), flags=re.MULTILINE)

        if cleaned_code != original_page_code:
            with open(target_page_path, "w", encoding="utf-8") as f:
                f.write(cleaned_code)
            print(f"✅ Successfully patched: {target_page_path}")
            any_file_modified = True
        else:
            print(f"⏸️ Analysis complete for {target_page_path}, but no alterations were required.")

    # Final script system signals back to GitHub Actions
    if any_file_modified:
        print("\n🎉 Batch processing complete! One or more codebases updated.")
        sys.exit(0) # Exit code 0 tells GHA: Fixes applied, execute re-testing sweep
    else:
        print("\n⏸️ Evaluated all failure nodes but no modifications were made.")
        sys.exit(2)

if __name__ == "__main__":
    run_batch_allure_repair()
