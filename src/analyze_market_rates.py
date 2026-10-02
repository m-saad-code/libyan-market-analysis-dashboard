"""Analyze a synthetic currency and gold rates workbook.

This project demonstrates an offline, reproducible data-analysis workflow.
The bundled values are synthetic/fictional and must not be used for financial
or investment decisions.
"""
from __future__ import annotations

import argparse
from copy import copy
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

REQUIRED_COLUMNS = {
    "record_id",
    "date",
    "usd_buy_lyd",
    "usd_sell_lyd",
    "eur_buy_lyd",
    "eur_sell_lyd",
    "gold_24k_lyd_per_gram",
    "gold_21k_lyd_per_gram",
    "currency",
    "market",
    "is_synthetic",
}
RATE_COLUMNS = [
    "usd_buy_lyd",
    "usd_sell_lyd",
    "eur_buy_lyd",
    "eur_sell_lyd",
    "gold_24k_lyd_per_gram",
    "gold_21k_lyd_per_gram",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and analyze a market-rates Excel workbook."
    )
    parser.add_argument("input", type=Path, help="Input .xlsx workbook")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for the enriched workbook, charts, and report",
    )
    return parser.parse_args()


def load_rates(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input workbook was not found: {path}")
    if path.suffix.lower() != ".xlsx":
        raise ValueError("The input file must have an .xlsx extension.")

    data = pd.read_excel(path, sheet_name="Market Rates")
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    return data


def validate_data(data: pd.DataFrame) -> None:
    missing_columns = REQUIRED_COLUMNS - set(data.columns)
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(sorted(missing_columns))
        )
    if data.empty:
        raise ValueError("The Market Rates sheet contains no records.")
    if data["date"].isna().any():
        raise ValueError("One or more dates are invalid or missing.")
    if data["date"].duplicated().any():
        duplicate_dates = data.loc[data["date"].duplicated(), "date"].dt.date.tolist()
        raise ValueError(f"Duplicate dates found: {duplicate_dates}")
    if data[RATE_COLUMNS].isna().any().any():
        raise ValueError("Missing numeric values were found in the rate columns.")
    if not data[RATE_COLUMNS].apply(lambda col: pd.api.types.is_numeric_dtype(col)).all():
        raise ValueError("All rate columns must be numeric.")
    if (data[RATE_COLUMNS] <= 0).any().any():
        raise ValueError("Rates must be positive.")
    if (data["usd_sell_lyd"] < data["usd_buy_lyd"]).any():
        raise ValueError("USD sell rate cannot be lower than the USD buy rate.")
    if (data["eur_sell_lyd"] < data["eur_buy_lyd"]).any():
        raise ValueError("EUR sell rate cannot be lower than the EUR buy rate.")
    if not data["is_synthetic"].fillna(False).astype(bool).all():
        raise ValueError(
            "This demo expects synthetic data. Review the source before using it."
        )


def add_metrics(data: pd.DataFrame) -> pd.DataFrame:
    result = data.sort_values("date").reset_index(drop=True).copy()
    result["usd_spread_lyd"] = result["usd_sell_lyd"] - result["usd_buy_lyd"]
    result["eur_spread_lyd"] = result["eur_sell_lyd"] - result["eur_buy_lyd"]
    result["usd_midpoint_lyd"] = (
        result["usd_buy_lyd"] + result["usd_sell_lyd"]
    ) / 2
    result["eur_midpoint_lyd"] = (
        result["eur_buy_lyd"] + result["eur_sell_lyd"]
    ) / 2
    result["usd_buy_change_pct"] = result["usd_buy_lyd"].pct_change() * 100
    result["eur_buy_change_pct"] = result["eur_buy_lyd"].pct_change() * 100
    return result


def summary_rows(data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for column in RATE_COLUMNS + ["usd_spread_lyd", "eur_spread_lyd"]:
        values = data[column].astype(float)
        rows.append(
            {
                "metric": column,
                "minimum": values.min(),
                "maximum": values.max(),
                "average": values.mean(),
                "first_to_last_change_pct": (values.iloc[-1] - values.iloc[0])
                / values.iloc[0]
                * 100,
            }
        )
    return pd.DataFrame(rows)


def save_chart(
    data: pd.DataFrame,
    columns: Iterable[str],
    labels: Iterable[str],
    title: str,
    y_label: str,
    output_path: Path,
) -> None:
    plt.figure(figsize=(10, 5.5))
    for column, label in zip(columns, labels):
        plt.plot(data["date"], data[column], marker="o", linewidth=2, label=label)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(y_label)
    plt.grid(alpha=0.25)
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def create_charts(data: pd.DataFrame, charts_dir: Path) -> None:
    charts_dir.mkdir(parents=True, exist_ok=True)
    save_chart(
        data,
        ["usd_buy_lyd", "usd_sell_lyd"],
        ["USD buy", "USD sell"],
        "Synthetic USD Rates",
        "LYD",
        charts_dir / "usd_rates.png",
    )
    save_chart(
        data,
        ["eur_buy_lyd", "eur_sell_lyd"],
        ["EUR buy", "EUR sell"],
        "Synthetic EUR Rates",
        "LYD",
        charts_dir / "eur_rates.png",
    )
    save_chart(
        data,
        ["gold_24k_lyd_per_gram", "gold_21k_lyd_per_gram"],
        ["Gold 24K", "Gold 21K"],
        "Synthetic Gold Prices",
        "LYD per gram",
        charts_dir / "gold_prices.png",
    )
    save_chart(
        data,
        ["usd_spread_lyd", "eur_spread_lyd"],
        ["USD spread", "EUR spread"],
        "Synthetic Currency Spreads",
        "LYD",
        charts_dir / "currency_spreads.png",
    )


def write_report(data: pd.DataFrame, summary: pd.DataFrame, output_path: Path) -> None:
    start = data["date"].min().date()
    end = data["date"].max().date()
    report = f"""# Synthetic Market Rates Analysis

## Scope

This report demonstrates a reproducible Python workflow for validating,
transforming, summarizing, and visualizing an Excel dataset. The dataset
contains **{len(data)} records** from **{start}** through **{end}**.

> The values are synthetic/fictional. They are not factual market quotations,
> financial advice, or evidence about Libya's real currency or gold market.

## Data-quality checks

- Required columns: present.
- Missing dates and numeric values: none detected.
- Duplicate dates: none detected.
- Negative or zero rates: none detected.
- Sell rates below buy rates: none detected.
- Synthetic flag: all records are marked synthetic.

## Key observations in this demo dataset

- Average USD spread: **{data['usd_spread_lyd'].mean():.3f} LYD**.
- Average EUR spread: **{data['eur_spread_lyd'].mean():.3f} LYD**.
- USD buy-rate first-to-last change: **{(data['usd_buy_lyd'].iloc[-1] / data['usd_buy_lyd'].iloc[0] - 1) * 100:.2f}%**.
- EUR buy-rate first-to-last change: **{(data['eur_buy_lyd'].iloc[-1] / data['eur_buy_lyd'].iloc[0] - 1) * 100:.2f}%**.

These observations describe the supplied synthetic records only. They must not
be generalized to the real market.

## Deliverables

The pipeline produces an enriched workbook, a summary table, four PNG charts,
and this report. It is intended as a portfolio demonstration of Python,
Pandas, validation, Excel handling, and data visualization.
"""
    output_path.write_text(report, encoding="utf-8")
    summary.to_csv(output_path.with_name("summary_metrics.csv"), index=False)


def export_workbook(data: pd.DataFrame, summary: pd.DataFrame, output_path: Path) -> None:
    metadata = pd.DataFrame(
        {
            "field": ["dataset_type", "disclaimer", "records", "analysis_scope"],
            "value": [
                "Synthetic / fictional",
                "Not for financial decisions",
                len(data),
                "Validation, derived metrics, and descriptive summaries",
            ],
        }
    )
    with pd.ExcelWriter(output_path, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
        data.to_excel(writer, sheet_name="Analyzed Rates", index=False)
        summary.to_excel(writer, sheet_name="Summary Metrics", index=False)
        metadata.to_excel(writer, sheet_name="About", index=False)
        for sheet in writer.sheets.values():
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column_cells in sheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 34)
        for sheet_name in ("Analyzed Rates", "Summary Metrics"):
            for cell in writer.sheets[sheet_name][1]:
                font = copy(cell.font)
                font.bold = True
                cell.font = font


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = load_rates(args.input)
    validate_data(data)
    analyzed = add_metrics(data)
    summary = summary_rows(analyzed)
    export_workbook(analyzed, summary, args.output_dir / "analyzed_market_rates.xlsx")
    create_charts(analyzed, args.output_dir / "charts")
    write_report(analyzed, summary, args.output_dir / "analysis_report.md")
    print(f"Validated and analyzed {len(analyzed)} synthetic records.")
    print(f"Outputs written to: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
