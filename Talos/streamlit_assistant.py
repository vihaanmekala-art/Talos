"""
Project: Talos v1.1.0
Description: Multi-functional financial analysis hub.
License: Proprietary. All rights reserved.
"""

from __future__ import annotations

import random

import streamlit as st
import yfinance as yf

from ai import calculate
from analysis import stocks, stock_analysis
from macro import show_macro
from portfolio import port
from valuation import intr


def main() -> None:
    st.sidebar.title("Talos v1.1.0")
    st.title("Talos v1.1.0")

    options = [
        "\U0001F3E0 Home Page",
        "\U0001F9E0 Calculate an Expression",
        "\U0001F4C8 Stock Analysis",
        "\u2696 Portfolio Optimizer",
        "\U0001F4CA Intrinsic Value",
        "\U0001F310 Macro Information",
        "\U0001F4CA Options Chain",
    ]

    option = st.sidebar.radio(
        "Options",
        options=options,
        label_visibility="collapsed",
    )

    if "current_option" not in st.session_state:
        st.session_state["current_option"] = option

    if st.session_state["current_option"] != option:
        st.session_state["current_option"] = option
        st.rerun()

    theme = st.sidebar.radio("Select a Theme", ["Light", "Dark [Beta]"])
    if theme == "Light":
        st.markdown(
            """
            <style>
            .stApp { background-color: #FFFFFF; color: #000000; }
            [data-testid="stSidebar"] { background-color: #F0F2F6; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.caption("Some elements may not be seen.")
        st.markdown(
            """
            <style>
            .stApp { background-color: #0E1117; }
            .stApp, .stMarkdown, .stText, .stMetric, .stSubheader,
            .stHeader, .stCaption, p, div, span, label { color: #FFFFFF !important; }
            [data-testid="stSidebar"] { background-color: #262730; }
            [data-testid="stMetricValue"] { color: #FFFFFF !important; }
            input, textarea { color: #FFFFFF !important; background-color: #262730 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    if option != "\U0001F4C8 Stock Analysis":
        st.session_state["stock"] = False

    if option == "\U0001F3E0 Home Page":
        col2, col3 = st.columns(2)
        with col2:
            st.subheader("AI insights.")
            tips = [
                "Use 'Golden Cross' signals for long-term stock trends.",
                "Always check the RSI before buying a big price jump.",
                "Keep your RAM usage below 80% for the best coding speed.",
                "Python's 'Pandas' library is named after 'Panel Data'!",
            ]
            random.shuffle(tips)
            st.write(tips[-1])
            if st.button("Generate a Fact"):
                st.write(tips[-1])

    elif option == "\U0001F9E0 Calculate an Expression":
        st.write("This was made possible with the Sympy Library.")
        st.write("Format trig ratios as Sin(30) or Cos(85)")
        question = st.text_input("Ask a math question:")
        answer = calculate(question)
        st.success(answer)

    elif option == "\U0001F4C8 Stock Analysis":
        file = st.file_uploader("Choose a JSON or CSV file.", type=["json", "csv"])
        if file is not None:
            stock_analysis(file)
        else:
            st.info("Or you can use the built-in stock analysis function!")
            if st.button("Type stock ticker"):
                st.session_state["stock"] = True

            if st.session_state.get("stock", False):
                stocks()

    elif option == "\u2696 Portfolio Optimizer":
        try:
            tickers_input = st.text_input("Choose 2+ stocks separated by commas. Format as AAPL, NVDA.")
            tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            if st.button("Optimize"):
                with st.spinner("Hunting for alpha..."):
                    fig, max_sharpe_df, min_vol, tickers = port(tickers)

                    col1a, col2a = st.columns(2)
                    with col1a:
                        st.subheader("Max Sharpe Portfolio")
                        st.metric("Expected Return", f"{max_sharpe_df['returns']:.2%}")
                        st.metric("Expected Risk", f"{max_sharpe_df['risk']:.2%}")
                        st.metric("Sharpe Ratio", f"{max_sharpe_df['sharpe']:.2f}")
                        st.write("**Allocations:**")
                        for ticker, w in zip(tickers, max_sharpe_df["Weight"]):
                            st.write(f"- {ticker}: {w:.1%}")
                    with col2a:
                        st.subheader("Min Volatility Portfolio")
                        st.metric("Expected Return", f"{min_vol['returns']:.2%}")
                        st.metric("Expected Risk", f"{min_vol['risk']:.2%}")
                        st.metric("Sharpe Ratio", f"{min_vol['sharpe']:.2f}")
                        st.write("**Allocations:**")
                        for ticker, w in zip(tickers, min_vol["Weight"]):
                            st.write(f"- {ticker}: {w:.1%}")

                    st.plotly_chart(fig)
                    st.warning("For educational purposes only. Not financial advice.")
        except TypeError:
            st.write("One of your tickers is invalid...")

    elif option == "\U0001F4CA Intrinsic Value":
        st.info("Note: When you update the slider, you will have to click the Calculate button again.")
        ticker = st.text_input("Type in your stock ticker.")

        col1, col2, col3 = st.columns(3)
        with col1:
            growth_rate = st.slider("FCF Growth Rate (%)", min_value=0, max_value=50, value=8, step=1) / 100
        with col2:
            discount_rate = st.slider("Discount Rate (%)", min_value=1, max_value=20, value=10, step=1) / 100
        with col3:
            terminal_growth = st.slider("Terminal Growth Rate (%)", min_value=0, max_value=10, value=3, step=1) / 100

        if st.button("Calculate"):
            if ticker:
                result = intr(ticker, growth_rate, discount_rate, terminal_growth)
            if result:
                intrinsic_value_per_share, current_price, df_proj, terminal_value_pv = result
                st.metric("Current Price", value=current_price)
                st.metric("Intrinsic Value", value=intrinsic_value_per_share)
                st.metric("Terminal Value", value=f"{terminal_value_pv:.2f}B")
                st.dataframe(df_proj)
                if intrinsic_value_per_share > current_price * 1.15:
                    verdict = "Undervalued"
                elif intrinsic_value_per_share < current_price * 0.85:
                    verdict = "Overvalued"
                else:
                    verdict = "Fairly Valued"
                st.subheader(verdict)
            st.warning("For educational purposes only. Not financial advice.")

    elif option == "\U0001F310 Macro Information":
        with st.spinner("Crunching Data..."):
            show_macro()

    elif option == "\U0001F4CA Options Chain":
        stock = st.text_input("Choose a Stock. Format as NVDA.")
        if stock:
            yf_ticker = yf.Ticker(stock)
            price = yf_ticker.info.get("currentPrice", "N/A")
            expirations = yf_ticker.options
            if expirations:
                choice = st.selectbox("Choose an Expiry Date", options=expirations)
                st.metric("Current Price", value=f"${price}")
                chain = yf_ticker.option_chain(choice)
                calls = chain.calls
                puts = chain.puts
                important_cols = [
                    "strike",
                    "lastPrice",
                    "bid",
                    "ask",
                    "volume",
                    "openInterest",
                    "impliedVolatility",
                ]
                st.subheader("Call Options")
                st.dataframe(calls[important_cols])
                st.subheader("Put Options")
                st.dataframe(puts[important_cols])
            else:
                st.error("No options data available for this ticker.")


if __name__ == "__main__":
    main()
