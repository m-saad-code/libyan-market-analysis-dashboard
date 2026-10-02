# Libyan Market Analysis Dashboard

A Streamlit demo for validating and analyzing Excel market-rate data.

> The bundled dataset is synthetic. It must not be treated as live Libyan market data, financial advice, or a factual market quotation source.

## Features

- Excel workbook upload
- Schema validation
- Date and missing-value checks
- Buy/sell consistency checks
- Currency spread calculations
- Summary metrics
- Trend charts
- CSV download

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-streamlit.txt
streamlit run app.py