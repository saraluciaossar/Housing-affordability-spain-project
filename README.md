# Housing Access in Spain — Are public first-home programs calibrated to the real market?

Interactive data-analysis project evaluating whether two Spanish public programs for first-home
access are well calibrated to actual housing market conditions: the **ICO mortgage guarantee**
(national) and the **Préstec Emancipació** (Catalonia). The analysis is structured across three
Jupyter notebooks (Block 1–3) and presented as an interactive **Streamlit + Plotly** app.

![Borrowing capacity by region and household profile](assets/screenshot_brecha_acceso.png)

## Hypotheses

- **H1 (Block 1):** The ICO price cap does not cover real transaction prices in the most
  strained regional markets.
- **H2 (Block 2):** Although the Préstec covers the nominal purchase price, the complementary
  mortgage (€200,000) is out of reach for single-applicant profiles at median salary.
- **H3 (Block 3):** The permanent HPO (officially protected housing) resale ceiling generates
  an accumulated wealth gap that exceeds the initial €50,000 loan benefit over 30 years.

## Methodology

- **Borrowing capacity:** standard mortgage model — 3.25% fixed rate, 25-year term, maximum
  35% debt-to-income ratio on net income (Bank of Spain criterion), 0.78 gross-to-net factor.
  Couple profiles assume two full-time median salaries (optimistic scenario).
- **30-year projection (Block 3):** provincial historical CAGR 2013–2024 as free-market
  appreciation proxy; median historical CPI (1.95%) as the HPO resale ceiling growth rate.
  Deterministic model with ±1 pp sensitivity analysis.
- **Data limitation:** prices are regional/provincial averages without distributional data,
  so the real access gap in high-pressure markets may be underestimated.

## Sign convention

Negative gap = problem (price exceeds cap / profile cannot access mortgage) → **red**.  
Positive gap = program covers the market → shown in green/teal.  
Convention is consistent across all visualizations and underlying data.

## Data sources

- Colegio de Registradores — residential transaction prices by region
- Idescat / Departament de Territori — Catalan provincial prices and CPI series
- INE Annual Wage Structure Survey — salaries for the 25–34 age bracket by sex and region
- Official ICO and ICF program terms and conditions

## Project structure
Housing-affordability-spain-project/

├── app.py                  # Streamlit app (light theme, Plotly charts)
├── Data/                   # raw sources + processed CSVs (b1_, b2_, b3_*)
├── Notebooks/              # three analysis blocks
├── .streamlit/config.toml  # theme configuration
├── requirements.txt
└── README.md

Processed DataFrames are exported from the notebooks to `Data/` as CSVs prefixed `b1_`, `b2_`,
`b3_` and loaded in the app via `@st.cache_data`.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
