# Housing Access in Spain — Are public first-home programs calibrated to the real market?

Interactive data-analysis project evaluating whether two Spanish public programs for first-home
access are well calibrated to the real housing market: the **ICO guarantee** (national) and the
**Préstec Emancipació** (Catalonia). The analysis lives in three Jupyter notebooks (Bloque 1–3) and
is presented as an interactive **Streamlit + Plotly** app.

## Hypotheses

- **H1 (Block 1):** the ICO price cap does not cover real prices in the most strained markets.
- **H2 (Block 2):** although the Préstec covers the nominal price, the complementary mortgage
  (€200,000) is out of reach for single-applicant profiles.
- **H3 (Block 3):** the permanent HPO (officially protected housing) price ceiling generates an
  accumulated wealth gap that exceeds the initial €50,000 loan benefit.

## Methodology

- **Borrowing capacity:** standard mortgage model — 3.25% rate, 25-year term, max. 35% effort ratio
  on net income (Bank of Spain criterion), 0.78 gross-to-net factor. Couples assume two full-time
  median salaries (optimistic scenario).
- **30-year projection (Block 3):** provincial historical CAGR 2013–2024 as free-market appreciation;
  median historical CPI (1.95%) as the HPO ceiling. Deterministic, with ±1pp sensitivity analysis.
- **Data limitation:** prices are CCAA/province averages, without distribution or percentiles, so the
  real gap in strained markets may be underestimated.

## Sign convention

Negative gap = problem (price exceeds cap / cannot access) → **red**. Positive = fine → **green**.
Kept consistent across the whole app.

## Sources

Colegio de Registradores (transaction prices), Idescat (Catalan comarcal prices and CPI),
INE — Annual Wage Structure Survey (salaries 25–34 by sex and region), official ICO / ICF terms.

## Project structure

```
Proyecto-prestamos-de-primera-vivienda-Espana/
├── app.py                  # Streamlit app (white theme, Plotly charts)
├── Data/                   # raw sources + processed b1_/b2_/b3_ CSVs
├── Notebooks/              # the 3 analysis blocks
├── .streamlit/config.toml  # light theme
├── requirements.txt
└── README.md
```

The processed DataFrames are exported from the notebooks to `Data/` as CSVs (`b1_*`, `b2_*`, `b3_*`)
and read by the app with `@st.cache_data`.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```
