I'm still working on it. Currently it works but it merely gives ipo result's output on terminal and is slow asf.

# NEPSE IPO Checker (Bulk) 🇳🇵

A Python-based utility for checking NEPSE IPO allotment results for multiple BOID accounts concurrently. The tool automates the verification workflow, supports multi-threaded execution, and stores results locally for later review.

---

## Features

* Check IPO allotment results for multiple BOIDs simultaneously
* Multi-threaded execution for faster processing
* Automated browser-based workflow
* AI-assisted captcha recognition using Gemini Vision
* Automatic retry handling for failed requests
* Saves result pages locally for reference
* Configurable thread count and account list

---

## Project Structure

```text
NEPSE_IPO_checker_bulk/
│
├── main.py
├── config.json
├── results/
│   ├── result_<boid>.html
│   └── ...
├── README.md
└── requirements.txt
```

---

## Requirements

* Python 3.10+
* Google AI Studio API Key
* Internet Connection

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/1Sujal/NEPSE_IPO_checker_bulk.git
cd NEPSE_IPO_checker_bulk
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If a requirements file is not available:

```bash
pip install camoufox pillow google-generativeai playwright
```

### 4. Install Browser Dependencies

```bash
playwright install firefox
```

---

## Configuration

Create a file named `config.json` in the project root.

```json
{
  "boids": [
    "1301010000000001",
    "1301010000000002",
    "1301010000000003"
  ],
  "threads": 3,
  "google_api_key": "YOUR_API_KEY"
}
```

### Configuration Fields

| Field          | Description                   |
| -------------- | ----------------------------- |
| boids          | List of BOID numbers to check |
| threads        | Number of concurrent workers  |
| google_api_key | Gemini API key                |

---

## Usage

Run the checker:

```bash
python main.py
```

The application will:

1. Load BOIDs from `config.json`
2. Launch concurrent workers
3. Process each account
4. Retrieve allotment results
5. Save responses locally

---

## Output

Results are stored inside the `results` directory:

```text
results/
├── result_1301010000000001.html
├── result_1301010000000002.html
└── result_1301010000000003.html
```

---

## Example

```json
{
  "boids": [
    "1301010000000001",
    "1301010000000002"
  ],
  "threads": 2,
  "google_api_key": "AIza..."
}
```

Run:

```bash
python main.py
```

---

## Notes

* Ensure your BOID numbers are entered correctly.
* Keep your API key private.
* Do not commit `config.json` containing sensitive credentials to public repositories.

---

## Recommended .gitignore

```gitignore
venv/
results/
config.json

__pycache__/
*.pyc
*.pyo
*.pyd

.env
.idea/
.vscode/

playwright-report/
```

---

## Disclaimer

This project is provided for educational and personal-use purposes. Users are responsible for complying with all applicable terms, policies, and regulations associated with any services they access.

---

## License

MIT License
