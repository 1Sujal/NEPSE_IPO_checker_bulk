import json
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

from captcha_solver import solve_captcha
from browser import run_browser_session


CONFIG_FILE = Path("config.json")


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print(f"[main] ERROR: {CONFIG_FILE} not found.")
        print("[main] Please create config.json with keys: boids, threads, google_api_key")
        sys.exit(1)

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    # Validate required fields
    if "boids" not in config or not config["boids"]:
        print("[main] ERROR: 'boids' list is missing or empty in config.json")
        sys.exit(1)

    # API key: config file takes precedence, then env var
    api_key = config.get("google_api_key", "").strip()
    if not api_key or api_key == "YOUR_GOOGLE_API_KEY_HERE":
        api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("[main] ERROR: No Google API key found.")
        print("[main] Set 'google_api_key' in config.json or export GOOGLE_API_KEY=...")
        sys.exit(1)

    config["_resolved_api_key"] = api_key
    config.setdefault("threads", 1)

    return config


def process_boid(boid: str, api_key: str) -> dict:
    """Worker function — runs a full browser session for one BOID."""
    print(f"\n[main] ▶ Starting check for BOID: {boid}")

    # Partial-apply api_key so captcha_solver_fn only takes b64 string
    solver_fn = partial(solve_captcha, api_key=api_key)

    result = run_browser_session(boid=boid, captcha_solver_fn=solver_fn)

    if result["success"]:
        print(f"[main] ✅ BOID {boid} — result saved to: {result['result_file']}")
    else:
        err = result.get("error", "Unknown error")
        print(f"[main] ❌ BOID {boid} — FAILED: {err}")

    return result


def print_summary(results: list[dict]):
    print("\n" + "=" * 60)
    print("  IPO ALLOTMENT CHECK — SUMMARY")
    print("=" * 60)
    for r in results:
        status = "✅ SUCCESS" if r["success"] else "❌ FAILED"
        if r["success"]:
            allotted = r.get("allotted")
            allot_str = "🎉 ALLOTTED" if allotted else ("❌ NOT ALLOTTED" if allotted is False else "❓ UNKNOWN")
        else:
            allot_str = "—"
        captcha = r.get("captcha", "N/A")
        file_out = r.get("result_file") or r.get("error", "—")
        print(f"  BOID      : {r['boid']}")
        print(f"  Status    : {status}")
        print(f"  Allotment : {allot_str}")
        print(f"  Captcha   : {captcha}")
        print(f"  Output    : {file_out}")
        print("-" * 60)

def main():
    print("[main] Loading config...")
    config = load_config()

    boids = config["boids"]
    threads = int(config["threads"])
    api_key = config["_resolved_api_key"]

    print(f"[main] BOIDs to check : {len(boids)}")
    print(f"[main] Threads        : {threads}")
    print(f"[main] API key        : {'*' * 8}{api_key[-4:]}")
    print()

    all_results = []

    if threads == 1 or len(boids) == 1:
        # Single-threaded path (simpler, better for debugging)
        for boid in boids:
            result = process_boid(boid, api_key)
            all_results.append(result)
    else:
        # Multi-threaded path
        with ThreadPoolExecutor(max_workers=min(threads, len(boids))) as executor:
            futures = {
                executor.submit(process_boid, boid, api_key): boid
                for boid in boids
            }
            for future in as_completed(futures):
                boid = futures[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    print(f"[main] EXCEPTION for BOID {boid}: {e}")
                    all_results.append({"boid": boid, "success": False, "error": str(e)})

    print_summary(all_results)


if __name__ == "__main__":
    main()