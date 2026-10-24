# Evidence Analyst

An inspectable CSV analysis workbench: upload data, review quality checks, ask a question, compare a regression model with a baseline, and export tables for Power BI.

![CI](https://github.com/sravanni369/evidence-analyst/actions/workflows/test.yml/badge.svg)

**Stack:** Python · pandas · scikit-learn · Streamlit · DSPy · E2B · Power BI (PBIP/DAX) · pytest · GitHub Actions

## Screenshots

All screenshots are real output from the bundled synthetic dataset, not mockups.

| Ask a question (offline mode) | Data quality profile |
|---|---|
| ![Revenue by region answer in the app](docs/app.png) | ![Column profile showing missing and unique counts](docs/data-quality.png) |

| ML baseline: Random Forest vs mean prediction | Automated test suite |
|---|---|
| ![Model MAE 42.66 vs baseline MAE 392.46](docs/ml-baseline.png) | ![17 tests passing](docs/tests.png) |

**Native Power BI report** (Power BI Desktop, `powerbi/project/EvidenceAnalyst.pbip`):

![Power BI report, all regions: 200 orders, $98,108.25 revenue](docs/dashboard.png)

Region slicer set to East (51 orders, $28,040.50, which matches the app's Revenue by region answer):

![Power BI report filtered to East](docs/dashboard-east.png)

## Run

Python 3.11+ recommended. From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Offline artifact reproduction (only pandas and scikit-learn required):

```powershell
python demo.py
```

Full automated suite (install requirements.txt first):

```powershell
python -m pytest -q
```

The sample contains 201 synthetic retail rows, one exact duplicate and one missing region. Cleaning removes the duplicate and preserves the missing value. No real customers or financial outcomes are represented.

## Two analysis paths

Offline mode supports four explicit question forms: `How many rows?`, `Show missing values`, `Summarize numeric columns`, and `Revenue by region`. These are fixed functions, not LLM output.

AI mode uses a DSPy typed signature to generate Python from column names/types and the question. Review the generated code, then authorize uploading the CSV to an isolated E2B sandbox. The sandbox runs pandas/scikit-learn code and returns answer.csv. Generated Python never executes on the app host. No dataset rows are intentionally sent to the LLM, but schema names and the question are; E2B receives the full cleaned CSV.

Set service credentials in the terminal before launching; never commit them:

```powershell
$env:LLM_MODEL = 'provider/model'
# Set the provider API key in its standard environment variable.
$env:E2B_API_KEY = 'your-key'
```

DSPy generates code here; no DSPy optimizer training or improvement claim is made. E2B and the LLM require accounts and may incur charges. Use synthetic/non-sensitive data only.

## ML evaluation

Numeric regression uses a fixed random holdout, training-only median imputation, a Random Forest, and a mean-prediction baseline. Exact duplicate predictor/target records are removed before splitting. Rows without a target are excluded. Displayed train/test counts therefore can be smaller than the cleaned row count. This is an educational demo, not a general AutoML system. IDs, target-derived features and time/group leakage still require manual review. The retail target is calculated from units, price and discount: its easy predictability is not evidence of business impact.

## Boundaries and current status

- 17 automated tests pass, covering the core, Streamlit interactions, uploaded-dataset changes, and mocked sandbox cleanup. A real DSPy signature is tested with a scripted model.
- AI adapter follows official APIs but live cloud execution needs credentials and remains unverified until run.
- A native Power BI project is included at `powerbi/project/EvidenceAnalyst.pbip`, with embedded synthetic data, DAX measures and nine visuals. See `powerbi/README.md` and `VALIDATION.txt` for Desktop validation status.
- UI verification status is recorded in VALIDATION.txt.
- File limit: 5 MB at the upload widget, 50,000 rows and 100 columns checked after CSV parsing. This is not a hardened public upload service.
- E2B internet access is disabled and sandbox lifetime/execution are bounded. Import lint is not a security sandbox. Generated code can still manipulate data and files inside its sandbox; inspect results.
- CSV formula prefixes in text cells are escaped on export. No authentication, rate limits, durable audit store, or production deployment is included.
- Computer vision is deferred. A future extension can convert image detections to tabular counts for this same analysis workflow.

## Architecture

`Streamlit → pandas validation/cleaning → fixed analysis OR DSPy → reviewed code → E2B → result table → CSV bundle → Power BI`

Each AI run uses a new sandbox, destroyed in a finally block. The provider API key is used by DSPy on the host and is not intentionally injected into the sandbox.

## Sources checked October 23, 2026

- [DSPy setup](https://dspy.ai/current/getting-started/installation/)
- [DSPy signatures](https://dspy.ai/current/getting-started/expanding-signatures/)
- [E2B quickstart](https://docs.e2b.dev/quickstart)
- [E2B file access](https://docs.e2b.dev/filesystem/read-write)
- [Power BI project report format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Microsoft's PBIR version 2 sample](https://github.com/microsoft/semantic-link-labs/blob/main/src/sempy_labs/report/_bpareporttemplate/definition/version.json)

## Power BI

Open `powerbi/project/EvidenceAnalyst.pbip` in Power BI Desktop and click Refresh if the data cache is empty. The model embeds only the bundled synthetic sample, so it needs no credentials or machine-specific CSV path. To use a new exported dataset, replace the Orders query in Power Query with cleaned.csv and preserve column names/types, or adapt the report to your schema.

The dashboard contains revenue, order count, average order value and units cards, regional revenue, a daily trend, a region slicer, a regional reconciliation table and a missing-region indicator. Null regions are presented as Unknown. Slicers affect the analytical metrics; the missing-region card explicitly counts Unknown and remains a dataset-quality indicator when another region is selected.

Rebuild definitions with `python scripts/build_powerbi.py` while the project is closed. Validate report JSON against Microsoft's published schemas with `python scripts/validate_powerbi.py` (requires internet). Desktop validation is still required after changes; schema validity alone does not guarantee rendering.

## Live integration check

After configuring provider credentials and E2B, run `python scripts/smoke_live.py`. It displays generated code, asks before executing it, and compares the cloud result with a known answer. It can incur service charges. No successful live call is claimed without executing this check.

## Interview demo (90 seconds)

1. Explain the problem: analysts need a traceable path from messy CSVs to an answer.
2. Show the duplicate and missing-value audit; explain why missing data stays visible.
3. Ask Revenue by region and inspect the resulting table.
4. Compare model MAE with the mean baseline; disclose synthetic data and random-split limits.
5. Export the bundle and explain the Power BI measures.
6. If credentials are configured, show DSPy-generated code and E2B execution. Otherwise explicitly label this path as unverified.
