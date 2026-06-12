import base64
import json
import tempfile
from PIL import Image
import google.generativeai as genai


def configure_gemini(api_key: str):
    """Configure Gemini with the provided API key."""
    genai.configure(api_key=api_key)


def decode_base64_captcha(b64_string: str, output_path: str = None) -> str:
    """
    Decode a base64-encoded captcha image and save it to disk.
    Returns the path to the saved image.
    """
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    image_data = base64.b64decode(b64_string)

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        output_path = tmp.name
        tmp.close()

    with open(output_path, "wb") as f:
        f.write(image_data)

    return output_path


def solve_captcha(b64_string: str, api_key: str) -> str:
    """
    Decode base64 captcha and solve with Gemini.
    Returns the solved captcha string (digits only).
    """
    configure_gemini(api_key)

    raw_path = decode_base64_captcha(b64_string, output_path="captcha_raw.png")
    print(f"[captcha_solver] Raw captcha saved to: {raw_path}")

    model = genai.GenerativeModel("gemini-2.5-flash")
    img = Image.open(raw_path)

    prompt = "Read the digits in this image. Only output the numbers, nothing else."
    response = model.generate_content([prompt, img])
    result = response.text.strip()

    digits_only = "".join(c for c in result if c.isdigit())[:5]
    print(f"[captcha_solver] Solved captcha: {digits_only}")

    return digits_only


if __name__ == "__main__":
    import sys

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    api_key = config["google_api_key"]

    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        with open(test_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        print(solve_captcha(b64, api_key))
    else:
        print("Usage: python captcha_solver.py <path_to_captcha_image>")