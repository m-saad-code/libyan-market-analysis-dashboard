from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Market Rates Analysis Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Market Rates Analysis Dashboard")
st.caption("Excel validation and analysis demo")

st.warning(
    "Demo only: the bundled data is synthetic and must not be treated "
    "as live Libyan market data or financial advice."
)

uploaded_file = st.file_uploader(
    "Upload an Excel workbook",
    type=["xlsx"],
)

if uploaded_file is not None:
    source = uploaded_file
elif Path("libyan_market_rates.xlsx").exists():
    source = "libyan_market_rates.xlsx"
elif Path("data/libyan_market_rates.xlsx").exists():
    source = "data/libyan_market_rates.xlsx"
else:
    st.info("Upload an Excel workbook to start.")
    st.stop()

try:
    data = pd.read_excel(source, sheet_name="Market Rates")

    required_columns = [
        "date",
        "usd_buy_lyd",
        "usd_sell_lyd",
        "eur_buy_lyd",
        "eur_sell_lyd",
        "gold_24k_lyd_per_gram",
        "gold_21k_lyd_per_gram",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        st.error("The workbook is missing required columns:")
        st.write(missing_columns)
        st.stop()

    data["date"] = pd.to_datetime(data["date"], errors="coerce")

    numeric_columns = [
        "usd_buy_lyd",
        "usd_sell_lyd",
        "eur_buy_lyd",
        "eur_sell_lyd",
        "gold_24k_lyd_per_gram",
        "gold_21k_lyd_per_gram",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    if data["date"].isna().any():
        st.error("The workbook contains invalid dates.")
        st.stop()

    if data[numeric_columns].isna().any().any():
        st.error("The workbook contains missing or invalid numeric values.")
        st.stop()

    if (data[numeric_columns] <= 0).any().any():
        st.error("Rates and gold prices must be greater than zero.")
        st.stop()

    if (data["usd_sell_lyd"] < data["usd_buy_lyd"]).any():
        st.error("At least one USD sell rate is lower than its buy rate.")
        st.stop()

    if (data["eur_sell_lyd"] < data["eur_buy_lyd"]).any():
        st.error("At least one EUR sell rate is lower than its buy rate.")
        st.stop()

    data["usd_spread_lyd"] = (
        data["usd_sell_lyd"] - data["usd_buy_lyd"]
    )

    data["eur_spread_lyd"] = (
        data["eur_sell_lyd"] - data["eur_buy_lyd"]
    )

    st.success("Validation passed successfully.")

    records, usd, eur, dates = st.columns(4)

    records.metric("Records", len(data))
    usd.metric(
        "USD average spread",
        f"{data['usd_spread_lyd'].mean():.3f} LYD",
    )
    eur.metric(
        "EUR average spread",
        f"{data['eur_spread_lyd'].mean():.3f} LYD",
    )
    dates.metric(
        "Date range",
        f"{data['date'].min().date()} → {data['date'].max().date()}",
    )

    data_tab, metrics_tab, charts_tab, quality_tab = st.tabs(
        [
            "Validated Data",
            "Summary Metrics",
            "Trend Charts",
            "Quality Notes",
        ]
    )

    with data_tab:
        st.subheader("Validated data")

        display_columns = [
            "date",
            "usd_buy_lyd",
            "usd_sell_lyd",
            "eur_buy_lyd",
            "eur_sell_lyd",
            "gold_24k_lyd_per_gram",
            "gold_21k_lyd_per_gram",
            "usd_spread_lyd",
            "eur_spread_lyd",
        ]

        display_data = data[display_columns].copy()
        display_data["date"] = display_data["date"].dt.strftime("%Y-%m-%d")

        display_data = display_data.rename(
            columns={
                "date": "Date",
                "usd_buy_lyd": "USD Buy (LYD)",
                "usd_sell_lyd": "USD Sell (LYD)",
                "eur_buy_lyd": "EUR Buy (LYD)",
                "eur_sell_lyd": "EUR Sell (LYD)",
                "gold_24k_lyd_per_gram": "Gold 24K (LYD/g)",
                "gold_21k_lyd_per_gram": "Gold 21K (LYD/g)",
                "usd_spread_lyd": "USD Spread (LYD)",
                "eur_spread_lyd": "EUR Spread (LYD)",
            }
        )

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True,
            height=450,
        )

        st.download_button(
            "Download analyzed CSV",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name="analyzed_market_rates.csv",
            mime="text/csv",
            type="primary",
        )

    with metrics_tab:
        st.subheader("Summary Metrics")

        summary = pd.DataFrame(
            {
                "Metric": [
                    "USD average buy",
                    "USD average sell",
                    "EUR average buy",
                    "EUR average sell",
                    "Gold 24K average",
                    "Gold 21K average",
                ],
                "Value": [
                    data["usd_buy_lyd"].mean(),
                    data["usd_sell_lyd"].mean(),
                    data["eur_buy_lyd"].mean(),
                    data["eur_sell_lyd"].mean(),
                    data["gold_24k_lyd_per_gram"].mean(),
                    data["gold_21k_lyd_per_gram"].mean(),
                ],
            }
        )

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True,
        )

    with charts_tab:
        st.subheader("Trend Charts")

        chart_data = data.set_index("date")

        left, right = st.columns(2)

        with left:
            st.markdown("**USD rates**")
            st.line_chart(
                chart_data[
                    ["usd_buy_lyd", "usd_sell_lyd"]
                ]
            )

            st.markdown("**Gold prices**")
            st.line_chart(
                chart_data[
                    [
                        "gold_24k_lyd_per_gram",
                        "gold_21k_lyd_per_gram",
                    ]
                ]
            )

        with right:
            st.markdown("**EUR rates**")
            st.line_chart(
                chart_data[
                    ["eur_buy_lyd", "eur_sell_lyd"]
                ]
            )

            st.markdown("**Currency spreads**")
            st.line_chart(
                chart_data[
                    ["usd_spread_lyd", "eur_spread_lyd"]
                ]
            )

    with quality_tab:
        st.subheader("Quality Notes")

        st.success("Schema check: passed")
        st.success("Date validation: passed")
        st.success("Missing-value check: passed")
        st.success("Positive-values check: passed")
        st.success("Buy/sell consistency check: passed")

        st.warning(
            "The current data is synthetic. It is suitable for a "
            "portfolio demonstration only."
        )

except ValueError as error:
    st.error("Could not read the required Excel sheet.")
    st.code(str(error))

except Exception as error:
    st.error("The workbook could not be analyzed.")
    st.code(str(error))
