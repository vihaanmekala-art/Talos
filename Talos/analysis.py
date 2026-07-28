"""
Stock analysis display functions.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.subplots
import streamlit as st
import yfinance as yf
from backtest import backtester

from tech import atr, bollinger, macd, rsi, sharpness, sim, wrap
from ai import groq


def stock_analysis(uploaded):
    st.write("Stock Analysis")

    if uploaded:
        try:
            if uploaded.name.endswith(".json"):
                df = pd.read_json(uploaded)
            elif uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)

            if "Date" not in df.columns or "Close" not in df.columns:
                st.error("You must have Date/Close columns.")
                return

            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date")

            st.dataframe(df.tail())

            start = df["Close"].iloc[-2]
            end = df["Close"].iloc[-1]
            stock_return = ((end - start) / start) * 100

            st.metric("Starting Price", f"${start:.2f}")
            st.metric("Ending Price", f"${end:.2f}")
            st.metric("Total Returns in percent", f"{stock_return:.2f}")

        except Exception as e:
            st.error("Something went wrong...")
            return f"Something went wrong...{e}"


def stocks():
    try:
        groq_key = st.text_input("Optional Groq key.", type="password")

        user = st.text_input("Choose a stock.").upper()
        user2 = st.date_input("Choose a starting date. Format as YYYY-MM-DD:")
        user3 = st.date_input("Choose a ending date. Format as YYYY-MM-DD:")

        if st.button("Run Stock Analysis"):
            if not user:
                st.error("Provide a ticker symbol.")
            else:
                df = yf.download(user, user2, user3, auto_adjust=True)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.reset_index()
                df["Date"] = pd.to_datetime(df["Date"])
                if df.empty:
                    st.error("Invalid ticker or API issue.")
                    return

                df = rsi(df)
                df = macd(df)
                df = bollinger(df)
                df = wrap(df)
                df = df.loc[:, ~df.columns.duplicated()]

                current_macd = df["MACD"].iloc[-1]
                sig_macd = df["Signal_Line"].iloc[-1]
                crossover = "Bullish" if current_macd > sig_macd else "Bearish"
                current_rsi = df["RSI"].iloc[-1]

                df = df[(df["Date"] >= pd.to_datetime(user2)) & (df["Date"] <= pd.to_datetime(user3))]
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                if df.empty:
                    st.error("Please provide a stock ticker.")
                    return

                def cagr(df, price_col: str) -> float:
                    start = df[price_col].iloc[0]
                    end = df[price_col].iloc[-1]
                    days = (df["Date"].iloc[-1] - df["Date"].iloc[0]).days
                    if days == 0 or start == 0:
                        return 0.0
                    return ((end / start) ** (365 / days) - 1) * 100

                stock_cagr = cagr(df, "Close")
                close = "Close"
                price = df[close].iloc[-1]
                last_close = df[close].iloc[-2]
                price_delta = price - last_close
                percent_delta = (price_delta / last_close) * 100

                df["SMA_100"] = df[close].rolling(window=100).mean()
                df["SMA_50"] = df[close].rolling(window=50).mean()

                ticker = yf.Ticker(user)
                info = ticker.info
                pe_ratio = info.get("trailingPE")
                forward_pe = info.get("forwardPE")
                marketcap = info.get("marketCap")
                dividend = info.get("dividendYield")
                debttoequity = info.get("debtToEquity")

                if df["SMA_50"].isna().iloc[-1]:
                    st.write("That is not enough range for 50 day SMA. Please choose a higher date range.")
                    return

                support = df[close].rolling(window=100).min()
                resistance = df[close].rolling(window=100).max()
                df["Support"] = support
                df["Resistance"] = resistance

                today_100 = df["SMA_100"].iloc[-1]
                today_50 = df["SMA_50"].iloc[-1]
                yesterday_100 = df["SMA_100"].iloc[-2]
                yesterday_50 = df["SMA_50"].iloc[-2]

                volume = df["Volume"]
                if isinstance(volume, pd.DataFrame):
                    volume = volume.iloc[:, 0]

                current_vol = float(volume.iloc[-1])
                vol_avg = float(volume.rolling(90).mean().iloc[-1])
                vol_ratio = current_vol / vol_avg

                df["Annual_Volatility"] = df["Close"].pct_change()
                annual_vol = df["Annual_Volatility"].std() * (252**0.5) * 100

                st.metric("Annual Volatility", f"{annual_vol:.2f}")
                st.metric("ATR", f"{atr(df)}")
                percent_distance_to_support = ((price - support.iloc[-1]) / support.iloc[-1]) * 100
                st.metric("Percent Away From 50 Day Low", f"{percent_distance_to_support:.2f}")

                from macro import get_risk_free
                risk_free = get_risk_free()

                st.metric("CAGR", f"{stock_cagr:.2f}")
                st.metric("Sharpe Ratio", f"{sharpness(df, risk_free)}")
                st.metric("RSI", f"{current_rsi:.2f}")
                st.metric("MACD", f"{current_macd:.2f}")

                if yesterday_100 <= yesterday_50 < today_50:
                    st.write("GOLDEN CROSS \u2728\uD83D\uDCC8")
                    st.balloons()
                elif yesterday_100 >= yesterday_50 > today_50:
                    st.write("DEATH CROSS \uD83D\uDCC9\u2620\uFE0F.")
                    st.snow()
                else:
                    if today_100 > today_50:
                        st.write("Bullish signs.")
                    else:
                        st.write("Bearish signs.")

                if vol_ratio > 1.5:
                    st.write("People are buying this stock more than usual! \uD83D\uDD25")
                elif vol_ratio < 0.5:
                    st.write("People are not buying this stock as much. \uD83E\uDDEA")
                elif pd.isna(vol_ratio):
                    st.write("Something went wrong when calculating the volume ratio.")

                if price > today_100:
                    st.write("Price is above the 100-day SMA.")
                else:
                    st.write("Price is below the 100-day SMA.")

                if price > today_50:
                    st.write("Price is above the 50-day SMA.")
                else:
                    st.write("Price is below 50-day SMA.")

                current_vwap = df["VWAP"].iloc[-1]
                if price > current_vwap:
                    st.write("Bullish Interday Bias")
                else:
                    st.write("Bearish Interday Bias")

                st.metric(label="Current Price", value=f"{price:.2f}", delta=f"{percent_delta:.2f}")
                st.metric("P/E Ratio", pe_ratio)
                st.metric("Forward P/E Ratio", forward_pe)
                st.metric("Market Cap", marketcap)
                st.metric("Dividend Yield", f"{dividend:.2%}" if dividend else "N/A")
                st.metric("Debt to Equity", debttoequity)

                try:
                    peg = float(pe_ratio) / float(stock_cagr)
                    st.metric("PEG Ratio", f"{peg:.2f}")
                except Exception:
                    st.error("Error Calculating PEG Ratio.")

                st.write(f"The MACD crossover is {crossover}.")
                if crossover == "Bearish":
                    st.snow()
                else:
                    st.balloons()

                st.session_state["backtest"] = backtester(df)
                back = st.session_state["backtest"]
                st.subheader("Backtest Results (Buy At RSI = 30, Sell At RSI = 70)")
                st.metric("Total Returns", value=f"{back['total_return']:.2f}%")
                st.metric("Sharpe Ratio", value=f"{back['sharpe']:.2f}")
                st.metric("Total Buys", f"{back['buy']}")
                st.metric("Total Sells", f"{back['sell']}")
                st.line_chart(back["portfolio"])

                if groq_key:
                    st.subheader("What the AI says [Beta]")
                    st.info(
                        groq(f"""
You are a Senior Equity Research Analyst. Your task is to provide a high-density, 4-sentence synthesis of market data for institutional clients.
Round all numbers to the nearest tenth.
Eliminate Filler: "Ban phrases like 'as evidenced by,', 'blind spot' 'the company's,' and 'representing a.' Use direct, punchy descriptors (e.g., 'Indefensible valuation' instead of 'The valuation appears stretched')."
Explicitly flag any 'Bullish/Bearish Divergence' when technicals are strong but growth is negative.
Bold the category at the start of each sentence (e.g., Posture:, Conviction:, Valuation:).
Use Financial Shorthand: "Instruct the AI to use terms like 'multiple expansion/contraction,' 'technical regime,' 'risk-reward skew,' and 'fundamental decay.'"
The "So What?" Rule: "Every sentence must lead with the conclusion, followed by the supporting data."
TECHNICAL INDICATORS:
- RSI: {current_rsi:.2f} (Oversold <30 | Neutral 30-70 | Overbought >70)
- MACD Crossover: {crossover} (Bullish if MACD crosses above signal line, Bearish if below)
- Annual Volatility: {annual_vol:.2f} (Low <20% | Moderate 20-40% | High >40%)
- Volume Ratio: {vol_ratio:.2f} (vs 20-day avg; >1.5 = elevated interest, <0.5 = weak conviction)
FUNDAMENTAL INDICATORS:
- Trailing P/E Ratio: {pe_ratio} (Industry avg ~20-25; higher = growth premium or overvaluation)
- Market Cap: {marketcap} (Market Cap ($100B+): Large/Mega-Cap; signifies an established, \"Blue Chip\" industry leader with high stability.
                        Market Cap (~$50M): Micro-Cap; signifies a high-risk, early-stage company with significant volatility and lower liquidity.)
- Dividend Yield: {dividend} (Dividend yield is a financial ratio, expressed as a percentage, that measures the annual dividend payment a company pays to shareholders relative to its current stock price.)
- CAGR: {stock_cagr:.2f} (Compound Annual Growth Rate; benchmark against S&P 500 ~10%)
- Debt To Equity: {debttoequity} ( A higher ratio indicates1 higher risk and greater reliance on borrowing, while a lower ratio signifies a more conservative, equity-funded structure.)
- PEG Ratio: {peg} (A low PEG ratio means you are paying a bargain price for a company's future growth, where a value under 1.0 suggests the stock is undervalued compared to its earnings potential.)
ANALYSIS GUIDELINES:
1. SYNTHESIZE: Do not recite data points in isolation; explain their interaction (e.g., how Volume confirms MACD).
2. PRECISION: Use 1-2 decimal places max. Avoid "decimal noise."
3. TONE: Be decisive and skeptical. Use "Bottom Line Up Front" (BLUF) logic.
4. VOLATILITY: Always frame volatility as a "risk-adjusted" hurdle, not just a number.
OUTPUT FORMAT (Exactly 4 sentences):
1. THE SETUP: Synthesize RSI, MACD, and Volume into a single market posture.
2. CONVICTION: Define the strength of the move based on the Volume Ratio/MACD spread.
3. VALUATION: Contextualize CAGR against P/E, P/B, or P/S; if data is missing, flag the "valuation blind spot."
4. THE VERDICT: A final risk-adjusted recommendation (e.g., 'Avoid,' 'Accumulate,' or 'Neutral') based on Volatility and contradictions.
""",
                            groq_key,
                        )
                    )

                plot_df = df.dropna(subset=["MACD", "Signal_Line", "MACD_Histogram"])
                if not plot_df.empty:
                    fig = plotly.subplots.make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.03,
                        subplot_titles=(f"{user} Stock Analysis", "MACD"),
                        row_width=[0.3, 0.7],
                    )

                    price_path, p5, p50, p95 = sim(df)
                    days = list(range(30))
                    fig_sim = go.Figure()

                    fig_sim.add_trace(
                        go.Scatter(
                            x=days,
                            y=p5,
                            fill="tonexty",
                            fillcolor="rgba(100, 149, 237, 0.3)",
                            line=dict(color="rgba(0,0,0,0)"),
                            name="5th\u201395th Percentile",
                        )
                    )

                    fig_sim.add_trace(
                        go.Scatter(
                            x=days,
                            y=p50,
                            line=dict(color="royalblue", width=2),
                            name="Median Path",
                        )
                    )

                    fig.add_trace(
                        go.Scatter(x=df["Date"], y=df["Close"], name="Closing Price", line=dict(color="gold", width=1)),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(x=df["Date"], y=df["SMA_50"], name="50 Day SMA", line=dict(color="orange", width=1)),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(x=df["Date"], y=df["SMA_100"], name="100 Day SMA", line=dict(color="orange", width=1)),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df["Date"],
                            y=df["BB_Up"],
                            line=dict(color="rgba(0,0,0,0)"),
                            showlegend=False,
                        ),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df["Date"],
                            y=df["BB_Down"],
                            line=dict(color="rgba(0,0,0,0)"),
                            fill="tonexty",
                            fillcolor="rgba(173, 216, 230, 0.2)",
                            name="Bollinger Band",
                        ),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Bar(x=df["Date"], y=df["MACD_Histogram"], name="Histogram"),
                        row=2,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(color="black")),
                        row=2,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(x=df["Date"], y=df["Signal_Line"], name="Signal", line=dict(color="red")),
                        row=2,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(x=df["Date"], y=df["VWAP"], name="VWAP", line=dict(color="red")),
                        row=1,
                        col=1,
                    )
                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=800,
                        template="plotly_white",
                        showlegend=True,
                    )

                    st.plotly_chart(fig, width="stretch")
                    st.plotly_chart(fig_sim, width="stretch")
                    st.subheader("Equity Curve")
                    st.write("The app is for educational/informational purposes, not financial advice.")
                    st.write("Talos AI is an experimental tool. Trading small-caps involves high risk of capital loss.")

                    html_buffer = fig.to_html()
                    st.download_button(
                        label="Download Report as HTML",
                        data=html_buffer,
                        file_name=f"{user}_analysis.html",
                        mime="text/html",
                    )

    except FileNotFoundError:
        st.error("The file was not found.")
    except PermissionError:
        st.error("You do not have permissions for this file.")
