import time
import random
from pathlib import Path
from camoufox.sync_api import Camoufox


BASE_URL = "https://iporesult.cdsc.com.np"
API_CAPTCHA_URL = f"{BASE_URL}/result/companyShares/fileUploaded"
RESULT_DIR = Path("results")


def ensure_result_dir():
    RESULT_DIR.mkdir(exist_ok=True)


def fetch_captcha_b64(page) -> dict:
    captcha_payload = {}

    def handle_response(response):
        nonlocal captcha_payload
        if "companyShares/fileUploaded" in response.url:
            try:
                body = response.json()
                captcha_info = (
                    body.get("body", {})
                        .get("captchaData", {})
                        .get("captcha", {})
                )
                if captcha_info:
                    captcha_payload = captcha_info
                    print("[browser] Captcha data intercepted from API response.")
            except Exception as e:
                print(f"[browser] Could not parse captcha response: {e}")

    page.on("response", handle_response)

    print(f"[browser] First visit to {BASE_URL} (cookie init)...")
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)

    print("[browser] Waiting for cookie-triggered page reload...")
    try:
        with page.expect_navigation(wait_until="networkidle", timeout=15000):
            pass
        print("[browser] Page reloaded after cookie init.")
    except Exception:
        print("[browser] No automatic reload detected; continuing...")
        page.wait_for_load_state("networkidle", timeout=15000)

    if not captcha_payload:
        print("[browser] Waiting for captcha API call...")
        page.wait_for_timeout(4000)

    if not captcha_payload:
        print("[browser] Still no captcha — forcing manual reload with cookies...")
        page.reload(wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(3000)

    return captcha_payload


def check_ipo_result(boid: str, captcha_text: str, page, result_filename: str) -> bool:
    ensure_result_dir()

    try:
        def human_click(selector: str):
            el = page.locator(selector)
            box = el.bounding_box()
            if box:
                target_x = box["x"] + box["width"] * (0.3 + 0.4 * (time.time() % 1))
                target_y = box["y"] + box["height"] * (0.3 + 0.4 * (time.time() % 1))
                page.mouse.move(target_x - 120, target_y - 60)
                page.wait_for_timeout(random.randint(80, 180))
                page.mouse.move(target_x, target_y, steps=random.randint(8, 15))
                page.wait_for_timeout(random.randint(50, 150))
                page.mouse.click(target_x, target_y)
            else:
                el.click()

        # Click BOID field then type
        print(f"[browser] Filling BOID: {boid}")
        page.wait_for_selector("#boid", timeout=10000)
        human_click("#boid")
        page.wait_for_timeout(random.randint(100, 250))
        page.fill("#boid", boid)

        # Click captcha field then type
        print(f"[browser] Filling captcha: {captcha_text}")
        page.wait_for_selector("#userCaptcha", timeout=10000)
        human_click("#userCaptcha")
        page.wait_for_timeout(random.randint(100, 250))
        page.fill("#userCaptcha", captcha_text)

        # Small delay to mimic human
        page.wait_for_timeout(random.randint(400, 700))

        # Click submit
        print("[browser] Moving mouse to submit button...")
        submit_btn = page.locator("button[type='submit']")
        box = submit_btn.bounding_box()
        if box:
            target_x = box["x"] + box["width"] * (0.3 + 0.4 * (time.time() % 1))
            target_y = box["y"] + box["height"] * (0.3 + 0.4 * (time.time() % 1))
            page.mouse.move(target_x - 120, target_y - 60)
            page.wait_for_timeout(random.randint(80, 180))
            page.mouse.move(target_x, target_y, steps=random.randint(8, 15))
            page.wait_for_timeout(random.randint(50, 150))
            page.mouse.click(target_x, target_y)
        else:
            submit_btn.click()

        # Wait for result to load
        page.wait_for_timeout(3000)

        # Save full page HTML
        html_content = page.content()
        result_path = RESULT_DIR / result_filename
        result_path.write_text(html_content, encoding="utf-8")
        print(f"[browser] Result saved to: {result_path}")

        try:
            result_text = page.inner_text("body")
            if "allot" in result_text.lower():
                print(f"[browser] Result snippet: {result_text[:300]}")
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"[browser] Error during form submission for BOID {boid}: {e}")
        try:
            html_content = page.content()
            error_path = RESULT_DIR / f"error_{boid}.html"
            error_path.write_text(html_content, encoding="utf-8")
            print(f"[browser] Error page saved to: {error_path}")
        except Exception:
            pass
        return False


def run_browser_session(boid: str, captcha_solver_fn) -> dict:
    result = {"boid": boid, "success": False, "result_file": None, "captcha": None}

    MAX_ATTEMPTS = 10

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[browser] Attempt {attempt}/{MAX_ATTEMPTS} for BOID {boid}")

        with Camoufox(headless=False, geoip=True) as browser:
            page = browser.new_page()

            captcha_data = fetch_captcha_b64(page)

            if not captcha_data:
                print(f"[browser] No captcha data on attempt {attempt}, retrying...")
                continue

            # Extract base64 string
            b64_captcha = None
            if isinstance(captcha_data, str):
                b64_captcha = captcha_data
            elif isinstance(captcha_data, dict):
                for key in ("image", "data", "base64", "captchaImage", "img"):
                    if key in captcha_data:
                        b64_captcha = captcha_data[key]
                        break
                if not b64_captcha and captcha_data:
                    b64_captcha = next(iter(captcha_data.values()))

            if not b64_captcha:
                print(f"[browser] Could not extract base64 on attempt {attempt}, retrying...")
                continue

            # Solve captcha
            print(f"[browser] Solving captcha (attempt {attempt})...")
            captcha_text = captcha_solver_fn(b64_captcha)
            result["captcha"] = captcha_text

            if not captcha_text or len(captcha_text) < 4:
                print(f"[browser] Bad captcha solve: '{captcha_text}', retrying...")
                continue

            # Submit form
            result_filename = f"result_{boid}.html"
            success = check_ipo_result(boid, captcha_text, page, result_filename)

            if not success:
                print(f"[browser] Form submission failed on attempt {attempt}, retrying...")
                continue

            # Check outcome
            try:
                page_text = page.inner_text("body")
            except Exception:
                page_text = ""

            if "not allot" in page_text.lower():
                print(f"[browser] ❌ Not allotted for BOID {boid}.")
                result["success"] = True
                result["allotted"] = False
                result["result_file"] = str(RESULT_DIR / result_filename)
                break
            elif "alloted" in page_text.lower() or "allotted" in page_text.lower():
                print(f"[browser] ✅ Allotted for BOID {boid}!")
                result["success"] = True
                result["allotted"] = True
                result["result_file"] = str(RESULT_DIR / result_filename)
                break
            elif "invalid captcha" in page_text.lower():
                print(f"[browser] Invalid captcha on attempt {attempt}, retrying...")
                continue
            else:
                print(f"[browser] Ambiguous result on attempt {attempt}, restarting browser...")
                continue

    else:
        print(f"[browser] Exhausted {MAX_ATTEMPTS} attempts for BOID {boid}.")
        result["error"] = f"Failed after {MAX_ATTEMPTS} attempts"

    return result