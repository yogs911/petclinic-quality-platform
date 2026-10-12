import os
import json
import glob
import re
import sys
import time
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

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

def call_gemini_with_fallback(client, prompt, system_instruction):
    """
    Executes the generation call using modern stable Gemini 3 series configurations, 
    with built-in exponential backoff retries and fallback models.
    """
    # Active Gemini 3 ecosystem production models
    models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash"]
    max_retries = 3
    initial_delay = 4  # seconds

    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                print(f"   🤖 Requesting {model_name} (Attempt {attempt + 1}/{max_retries})...")
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        # Note: Gemini 3 API strips traditional sampling params (temp/top_p) 
                        # to optimize uniform coding determinism via native presets.
                        thinking_config=types.ThinkingConfig(thinking_level="medium")
                    )
                )
                return response.text.strip()

            except ServerError as e:
                # Intercept 503 capacity issues or 500 errors gracefully
                if "503" in str(e) or "unavailable" in str(e).lower() or "temporary" in str(e).lower():
                    delay = initial_delay * (2 ** attempt)  # 4s, 8s, 16s
                    print(f"   ⚠️ Server busy (503). Backing off for {delay}s before retrying...")
                    time.sleep(delay)
                else:
                    raise e
            except APIError as e:
                print(f"   ⚠️ API Error encountered on {model_name}: {e}")
                break  # Skip to next available fallback version

    print("❌ All Gemini free-tier fallback options are currently overloaded. Escalating to human engineering queue.")
    sys.exit(2)

def run_batch_allure_repair():
    failed_batches = gather_all_failed_allure_contexts()
    
    if not failed_batches:
        print("✅ No test failures found in Allure results. Pipeline is healthy.")
        sys.exit(2) # Signal to skip secondary execution run

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    system_instruction = (
        "You are an expert Playwright automation agent. Your sole purpose is fixing flaky selectors "
        "and synchronization issues within Page Object files inside the /pages directory. "
        "You must respond ONLY with the raw updated TypeScript code. Do not include markdown wraps or ``` blocks."
    )

    any_file_modified = False

    for target_page_path, error_logs in failed_batches.items():
        print(f"\n🎯 Processing failures targeting: {target_page_path}")
        print(f"   Collected {len(error_logs)} unique failure data tracks for this object.")
        
        with open(target_page_path, "r", encoding="utf-8") as f:
            original_page_code = f.read()

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

        raw_response = call_gemini_with_fallback(client, prompt, system_instruction)

        # Remove any markdown backticks if returned
        cleaned_code = re.sub(r'^```ts\s*|^```typescript\s*|^```\s*|```$', '', raw_response, flags=re.MULTILINE)

        if cleaned_code != original_page_code:
            with open(target_page_path, "w", encoding="utf-8") as f:
                f.write(cleaned_code)
            print(f"✅ Successfully patched: {target_page_path}")
            any_file_modified = True
        else:
            print(f"⏸️ Analysis complete for {target_page_path}, but no alterations were required.")

    if any_file_modified:
        print("\n🎉 Batch processing complete! One or more codebases updated.")
        sys.exit(0) # Triggers secondary evaluation sweep in GHA
    else:
        print("\n⏸️ Evaluated all failure nodes but no modifications were made.")
        sys.exit(2)

if __name__ == "__main__":
    run_batch_allure_repair()
