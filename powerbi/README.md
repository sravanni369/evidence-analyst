# Evidence Analyst Power BI report

Open **project/EvidenceAnalyst.pbip** in Power BI Desktop. Keep its Report and SemanticModel folders beside it. The model embeds the synthetic sample, so it needs no credentials or machine-specific CSV path.

On June 2025 Desktop, enable File > Options and settings > Options > Preview features > Store reports using enhanced metadata format (PBIR), then restart. Newer versions may support it by default. Report metadata version 2.0.0 matches Microsoft's sample and the tested installation.

Click Refresh when opening without a data cache. Reconcile all-data totals with project/reconciliation.json:

| Metric | Result |
|---|---:|
| Revenue | $98,108.25 |
| Orders | 200 |
| Average order value | $490.54 |
| Units | 2,031 |
| Missing region | 1 |

The revenue card can abbreviate to $98.11K; the regional table preserves cents. Region filters apply to the analytical metrics. The missing-region card explicitly counts Unknown, overriding the region slicer so the dataset-quality issue stays visible. Unknown is a presentation label for the one null region; the cleaned CSV retains its null.

Grain: one synthetic order. Revenue is already net of discount. Dates cover September 2026. This is demonstration data, not real company financial results.

To analyze new exports, replace the Orders query in Power Query with cleaned.csv and preserve expected names/types. Exporting a CSV does not automatically update the embedded sample.

Rebuild with python scripts/build_powerbi.py from the repository root while Power BI is closed. This overwrites generated project files. Validate JSON with python scripts/validate_powerbi.py, then reopen in Desktop and verify rendering. Schema validity alone does not prove a report works.
