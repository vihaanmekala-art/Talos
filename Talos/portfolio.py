"""
Portfolio optimization using Monte Carlo simulation.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from macro import get_risk_free


def port(tickers: list[str], num_port: int = 3000):
    df = yf.download(tickers, period="2y", auto_adjust=True)

    if df.empty:
        st.warning("Could not download data.")
        return None

    if isinstance(df.columns, pd.MultiIndex):
        prices = df["Close"]
    else:
        prices = df[["Close"]].rename(columns={"Close": tickers[0]})

    if prices.empty or len(prices.columns) < 2:
        st.warning("You need at least 2 tickers.")
        st.stop()
        return None

    returns = np.log(prices / prices.shift(1))
    mean = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    result = []
    weights = []
    assets = len(tickers)
    risk_free = get_risk_free()
    gene = np.random.default_rng()

    for _ in range(num_port):
        w = gene.random(assets)
        w = w / w.sum()
        weights.append(w)
        portfolio_return = np.dot(w, mean)
        portfolio_risk = np.sqrt(w.T @ cov_matrix.values @ w)
        sharpe = (portfolio_return - risk_free) / portfolio_risk

        result.append(
            {
                "returns": portfolio_return,
                "risk": portfolio_risk,
                "sharpe": sharpe,
                "Weight": w,
            }
        )

    result_df = pd.DataFrame(result)
    max_sharpe = result_df["sharpe"].idxmax()
    min_risk = result_df["risk"].idxmin()
    min_vol = result_df.iloc[min_risk]
    max_sharpe_df = result_df.iloc[max_sharpe]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result_df["risk"],
            y=result_df["returns"],
            mode="markers",
            marker=dict(
                color=result_df["sharpe"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Sharpe Ratio"),
                size=4,
                opacity=0.6,
            ),
            name="Chart of Portfolios",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[max_sharpe_df["risk"]],
            y=[max_sharpe_df["returns"]],
            mode="markers",
            marker=dict(color="red", size=15, symbol="star"),
            name=f"Max Sharpe: {max_sharpe_df['sharpe']:.2f}",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[min_vol["risk"]],
            y=[min_vol["returns"]],
            mode="markers",
            marker=dict(color="green", size=15, symbol="star"),
            name="Min Volatility",
        )
    )

    fig.update_layout(
        title="Efficient Frontier",
        xaxis_title="Annual Risk",
        yaxis_title="Annual Returns",
        xaxis=dict(tickformat=".0%"),
        yaxis=dict(tickformat=".0%"),
        height=600,
        template="plotly_white",
    )

    return fig, max_sharpe_df, min_vol, tickers
