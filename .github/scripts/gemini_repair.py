import os
import json
import glob
import re
import sys
import time
import subprocess
from google import genai
from google.genai import types
from google.genai.errors import ServerError, APIError

def gather_failed_allure_contexts(results_dir="report/allure-results"):
    """Scans the Allure results directory to find the current failures."""
    if not os.path.exists(results_dir):
        return {}

    failed_batches = {}
    result_files = glob.glob(os.path.join(results_dir, "*-result.json"))
    
    for file_path in result_files:
        with open(file_path, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        
        if test_data.get("status") in ["failed", "broken"]:
            status_details = test_data.get("statusDetails", {})
            error_log = status_details.get("message", "") + "\n" + status_details.get("trace", "")
            
            spec_file = "Unknown"
            for label in test_data.get("labels",):
                if label.get("name") == "suite":
                    spec_file = label.get("value", "")

            page_match = re.search(r"pages/[\w-]+\.ts", error_log)
            if page_match:
                target_page_path = page_match.group(0)
            else:
                base_name = os.path.basename(spec_file).replace(".spec.ts", "")
                target_page_path = f"pages/{base_name}.page.ts"

            if os.path.exists(target_page_path):
                if target_page_path not in failed_batches:
                    failed_batches[target_page_path] = {"errors": [], "spec": spec_file}
                failed_batches[target_page_path]["errors"].append(error_log)
                
    return failed_batches

def call_gemini(client, prompt, system_instruction):
    """Handles API calls to gemini-3.8-flash with 503 backoff protection."""
    max_retries = 3
    initial_delay = 4
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    thinking_config=types.ThinkingConfig(thinking_level="medium")
                )
            )
            return response.text.strip()
        except ServerError as e:
            if "503" in str(e) or "unavailable" in str(e).lower():
                delay = initial_delay * (2 ** attempt)
                print(f"   ⚠️ Gemini busy (503). Backing off for {delay}s...")
                time.sleep(delay)
            else:
                raise e
    print("❌ Gemini API unavailable after multiple retries.")
    return None

def execute_local_test(spec_file):
    """
    Runs a single failing spec file locally within an isolated sandbox directory.
    Keeps the master allure-results clean.
    """
    print(f"   ⚙️ Running local validation verification for: {spec_file}")
    
    # Direct the sandbox run to dump its data into an isolated temporary folder
    # This prevents overwriting or scrambling your master test tracking data
    sandbox_env = os.environ.copy()
    sandbox_env["ALLURE_RESULTS_DIR"] = "allure-sandbox-results"
    
    # Wipe any old sandbox data before running
    subprocess.run("rm -rf allure-sandbox-results/*", shell=True, capture_output=True)
    
    # Execute only this specific file sequentially
    result = subprocess.run(
        f"npx playwright test {spec_file}", 
        shell=True, 
        capture_output=True, 
        text=True,
        env=sandbox_env
    )
    return result.returncode == 0

# ... [Keep your existing gather, call_gemini, and execute_local_test logic identical] ...

def run_self_healing_loop():
    failed_batches = gather_failed_allure_contexts()
    if not failed_batches:
        print("✅ No test failures found in Allure results.")
        sys.exit(2)

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    system_instruction = (
        "You are an expert Playwright automation agent. Your sole purpose is fixing flaky selectors "
        "and synchronization issues within Page Object files inside the /pages directory. "
        "You must respond ONLY with the raw updated TypeScript code. Do not include markdown wraps or ``` blocks."
    )

    # Track which specific test files were successfully healed
    successfully_fixed_specs = []

    for target_page_path, metadata in failed_batches.items():
        spec_file = metadata["spec"]
        error_logs = metadata["errors"]
        
        print(f"\n🕵️ Target Page Object: {target_page_path}")
        print(f"🕵️ Target Spec File: {spec_file}")

        with open(target_page_path, "r", encoding="utf-8") as f:
            original_clean_code = f.read()

        current_code_under_test = original_clean_code
        loop_errors = "\n--- Next Instance ---\n".join(error_logs)
        
        healed = False
        for attempt in range(1, 4):
            print(f"\n🔄 Self-Healing Attempt {attempt}/3 for {target_page_path}...")

            prompt = f"""
            Optimize this Page Object code to resolve the following test execution failures.

            FAILURES OBSERVED:
            {loop_errors}

            CURRENT WORKING CODE CODE:
            {current_code_under_test}

            BOUNDED RULES:
            1. Target the selector (e.g. #lastName) or async timing flow causing the timeout.
            2. Never use raw page.waitForTimeout().
            3. Provide the COMPLETE code file content. No omissions.
            """

            raw_response = call_gemini(client, prompt, system_instruction)
            if not raw_response:
                break

            cleaned_code = re.sub(r'^```ts\s*|^```typescript\s*|^```\s*|```$', '', raw_response, flags=re.MULTILINE)

            with open(target_page_path, "w", encoding="utf-8") as f:
                f.write(cleaned_code)

            success = execute_local_test(spec_file)

            if success:
                print(f"✅ CONVERGED! The patch resolved the failure.")
                healed = True
                if spec_file not in successfully_fixed_specs:
                    successfully_fixed_specs.append(spec_file)
                break
            else:
                print(f"❌ REJECTED! Fix attempt {attempt} was incorrect.")
                new_failures = gather_failed_allure_contexts()
                if target_page_path in new_failures:
                    loop_errors = "\n--- New Bad Fix Errors ---\n".join(new_failures[target_page_path]["errors"])
                current_code_under_test = cleaned_code

        if not healed:
            print(f"⚠️ Agent could not converge on a valid fix. Rolling back.")
            with open(target_page_path, "w", encoding="utf-8") as f:
                f.write(original_clean_code)

    # --- NEW: WRITE TARGETED SPECS TO GITHUB ACTIONS OUTPUT ---
    if successfully_fixed_specs:
        # Join specs by space so Playwright can consume them inline: "tests/login.spec.ts tests/logout.spec.ts"
        specs_string = " ".join(successfully_fixed_specs)
        print(f"\n📢 Exposing successfully fixed specs to CI: {specs_string}")
        
        # Write to the special GitHub output file environment variable
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as fh:
                fh.write(f"fixed_specs={specs_string}\n")
        
        sys.exit(0) 
    else:
        sys.exit(2) 

if __name__ == "__main__":
    import sys
    run_self_healing_loop()

