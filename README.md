# Autolysis: Automated Dataset Analysis

**Autolysis** is a Python script that:
1. Takes a CSV dataset as input.
2. Performs basic data analysis:
   - Provides summary statistics.
   - Identifies missing values.
   - Creates up to three charts:
     - Correlation heatmap (if numeric columns are present).
     - Histogram for the first numeric column.
     - Bar plot of top categories for the first categorical column.
3. Encodes these charts in base64 and sends them to a Language Model (LLM) endpoint.
4. Receives a Markdown report from the LLM and saves it as `README.md`.

## Requirements

- Python 3.7+
- The Python packages listed in `requirements.txt`.

You can install the requirements using:
```bash
pip install -r requirements.txt
```

## Installing uv

The `uv` tool is used to run the script. Install `uv` using one of the methods below:

**Linux or macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, ensure `uv` is on your PATH. Once `uv` is installed, you can run the script as described in the Usage section.

## Usage

Once the requirements are installed and `uv` is set up, run:
```bash
uv run autolysis.py /path/to/file.csv
```
Replace `/path/to/file.csv` with the actual path to your CSV file.

**Example:**
```bash
uv run autolysis.py media.csv
```

After the script completes, you will have:

- Up to three PNG charts generated in the same directory as the CSV file.
- A `datasetname_README.md` file containing the LLM-generated report.

## Notes

Make sure you have a `.env` file with a valid `AIPROXY_TOKEN` before running.

The script is currently configured to use the LLM endpoint at:
```bash
http://aiproxy.sanand.workers.dev/openai/v1/chat/completions
```
and the model: `gpt-4o-mini`.

You can adjust these settings in the script if needed.

If no numeric or categorical data is found, fewer than three charts may be generated.