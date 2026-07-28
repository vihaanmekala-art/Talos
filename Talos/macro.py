"""
Macroeconomic data from FRED.
"""

import os

import requests
import streamlit as st


def get_fred_key() -> str | None:
    return os.environ.get("FRED_KEY") or st.secrets.get("FRED_KEY")


def get_macro(series_id: str) -> str | None:
    try:
        fred_key = get_fred_key()
        if not fred_key:
            st.error("FRED API key not configured. Set FRED_KEY in .streamlit/secrets.toml or environment variables.")
            return None

        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": fred_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 10,
        }
        response = requests.get(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        obsv = data["observations"]
        real_data = obsv[0]["value"]
        if real_data == ".":
            return None
        return real_data
    except requests.exceptions.ConnectionError:
        st.error("No internet.")
        return None
    except requests.exceptions.Timeout:
        st.error("Server took too long to respond.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"FRED API error: {e}")
        return None
    except Exception as e:
        st.error(f"Something went wrong... {e}")
        return None


@st.cache_data(persist="disk")
def get_risk_free() -> float:
    risk_free = get_macro("DGS10")
    try:
        return float(risk_free) / 100
    except (ValueError, TypeError):
        return 0.0422


def show_macro():
    try:
        gdp_growth = get_macro("A191RL1Q225SBEA")
        inflation = get_macro("CPIAUCSL")
        fed_funds = get_macro("FEDFUNDS")
        unemployed = get_macro("UNRATE")
        tres_yield = get_macro("DGS10")
        sp500 = get_macro("SP500")

        st.subheader("United States Macroeconomic Data")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("GDP Growth", value=f"{gdp_growth}%")
        with col2:
            st.metric("Inflation (CPI)", value=inflation)
        with col3:
            st.metric("Fed Interest Rates", value=f"{fed_funds}%")
        with col1:
            st.metric("Unemployment Rate", value=unemployed)
        with col2:
            st.metric("10 Year Treasury Yield", value=f"{tres_yield}%")
        with col3:
            st.metric("S&P 500 Price", value=f"${sp500}")
    except Exception:
        st.error("Something went wrong...")
