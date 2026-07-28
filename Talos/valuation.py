"""
DCF intrinsic value calculation.
"""

import streamlit as st
import pandas as pd
import yfinance as yf


def intr(ticker: str, growth_rate: float, discount_rate: float, terminal_growth_rate: float, years: int = 5):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        cash = stock.cashflow

        try:
            oper_cash = cash.loc["Operating Cash Flow"].iloc[0]
            capex = cash.loc["Capital Expenditure"].iloc[0]
            fcf = oper_cash + capex
        except Exception:
            st.error("Could not retrieve Free Cash Flow data for this ticker.")
            return None

        if fcf <= 0:
            st.warning(
                f"Free Cash Flow is negative (${fcf / 1e9:.2f}B). DCF may not be meaningful for this stock."
            )

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        shares_outstanding = info.get("sharesOutstanding")

        if not current_price or not shares_outstanding:
            st.error("Could not retrieve price.")
            return None

        proj = []
        fcf_curr = fcf

        for year in range(1, years + 1):
            fcf_proj = fcf_curr * (1 + growth_rate) ** year
            pres_val = fcf_proj / (1 + discount_rate) ** year
            proj.append(
                {
                    "Year": f"Year {year}",
                    "Projected FCF ($B)": fcf_proj / 1e9,
                    "Present Value ($B)": pres_val / 1e9,
                }
            )

        df_proj = pd.DataFrame(proj)
        final_fcf = fcf * (1 + growth_rate) ** years
        terminal_value = (
            final_fcf
            * (1 + terminal_growth_rate)
            / (discount_rate - terminal_growth_rate)
        )
        terminal_value_pv = terminal_value / (1 + discount_rate) ** years
        total_pv = df_proj["Present Value ($B)"].sum() * 1e9
        intrinsic_value_total = total_pv + terminal_value_pv
        intrinsic_value_per_share = intrinsic_value_total / shares_outstanding
        terminal_value_pv = terminal_value_pv / 1e9

        return intrinsic_value_per_share, current_price, df_proj, terminal_value_pv

    except Exception as e:
        st.error(f"{e}")
        return None
