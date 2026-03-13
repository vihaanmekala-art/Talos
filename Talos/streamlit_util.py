"""
Project: Talos v1.0.1
Description: Multi-functional AI & Financial Analysis Hub.
License: Proprietary / All Rights Reserved.
Copyright (c) [Vihaan Mekala] All rights reserved.
This software is proprietary. Resale or redistribution is strictly prohibited.

Users must have their own Alpha Vantage account and obey Alpha Vantage’s terms.
"""
import io
import time
import shutil
import requests
from pathlib import Path
import subprocess
import sympy as sp
import streamlit as st
import pandas as pd
import psutil
import platform
from matplotlib.backends.backend_pdf import PdfPages
from plotly.subplots import make_subplots
import sqlite3
import plotly.graph_objects as go
import numpy as np
import requests
import yfinance as yf

def grok(question, key):

    if not key:
        return "Error: API Key not found in environment variables."

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": question}]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    data = response.json()

    if response.status_code == 200:
        return data['choices'][0]['message']['content']
    else:
        return f"API Error {response.status_code}: {data.get('error', {}).get('message', 'Unknown error')}"
def sent(symbol, key):
    url = "https://www.alphavantage.co/query"
    param = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "apikey": key,
        "limit": 5
    }
    response = requests.get(url, params=param)
    data = response.json()
    print(data)

    if 'feed' not in data:
        return []
    results = []
    for a in data['feed']:
        results.append({'title':a['title'], 'sentiment':a['overall_sentiment_label'], 'score':a['overall_sentiment_score']})
    return results

def wrap(df):
    df = df.copy()
    try:
        df['Ty'] = (df['High'] + df['Low'] + df['Close']) / 3
    except ZeroDivisionError:
        return None

    df['Cum_TP_Vol'] = (df['Ty'] * df['Volume']).cumsum()

    df['Cum_Vol'] = df['Volume'].cumsum()

    df['VWAP'] = df['Cum_TP_Vol'] / df['Cum_Vol']

    return df 
def atr(df, period=14):
    df = df.copy()
    high_low = df['High'] - df['Low']
    high_prev_close = (df['High'] - df['Close'].shift(1)).abs()
    low_prev_close = (df['Low'] - df['Close'].shift(1)).abs()

    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1)
    tr = tr.max(axis=1)

    atr = tr.rolling(window=period).mean()
    return atr.iloc[-1]
def sharpness(df, risk_free = 0.0369):
    returns = df['Close'].dropna().pct_change().dropna()
    daily_rf = (1 + risk_free) ** (1/252) - 1
    mean = returns.mean()
    vola = returns.std()
    if vola == 0:
        return np.nan
    sharpe_ratio = ((mean - daily_rf) / vola) * np.sqrt(252)

    return sharpe_ratio


def sim(df):
    returns = df['Close'].dropna().pct_change()
    price = df['Close'].iloc[-1]

    vola = returns.std()
    ret = returns.mean()

    rng = np.random.default_rng()
 
    noise = rng.normal(ret, vola, (30, 1000))
    

    price_path = price * (1 + noise).cumprod(axis=0)
   
    p5 = np.percentile(price_path, 5, axis=1)
    p50 = np.percentile(price_path, 50, axis=1)
    p95 = np.percentile(price_path, 95, axis=1)


    return price_path, p5, p50, p95
def gauge(value, title, color='green'):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"},
                {'range': [80, 100], 'color': "darkred"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig
def bollinger(df, window=20, num_std=2):

    df = df.copy()
    df['SMA_20'] = df['Close'].rolling(window=window).mean()
    df['BB_Up'] = df['SMA_20'] + num_std * df['Close'].rolling(window=window).std()
    df['BB_Down'] = df['SMA_20'] - num_std * df['Close'].rolling(window=window).std()
    return df


def macd(df):
    emal12 = df['Close'].ewm(span=12, adjust=False).mean()
    emal26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = emal12 - emal26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
    return df

def rsi(df, period = 14):
    df = df.dropna()
    df['Close'] = pd.to_numeric(df['Close'], errors = 'coerce')
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods = period).mean()
    avg_loss = loss.rolling(window=period, min_periods = period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df



def get_ollama():
    path = shutil.which("ollama")
    if path:
        return path
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        win_path = home / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe"
        if win_path.exists():
            return str(win_path)
    elif system == "Darwin":
        mac_path = Path("/Applications/Ollama.app/Contents/Resources/ollama")
        if mac_path.exists():
            return str(mac_path)
    elif system == "Linux":
        linux_paths = ["/usr/local/bin/ollama", "/usr/bin/ollama", "/bin/ollama"]
        for path in linux_paths:
            if Path(path).exists():
                return path
    return None



ollama_path = get_ollama()
if ollama_path is None:
    st.error('Ollama not found. Please install it.')
    st.stop()


def check_time():
    return f"The time is {time.strftime('%H:%M:%S')}"


def gemma_ai(question):
    question = question.strip()
    the_time = time.strftime("%Y-%m-%d %H:%M:%S")
    prompt = (
        "Give a clear, concise answer in 5–8 sentences. "
        "Focus on key points and avoid unnecessary detail.\n\n"
        f"The current time is {the_time}"
        f"Question: {question}"
    )
    try:
        result = subprocess.run(
            [ollama_path, "run", "gemma3:1b", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            return f"Error: {result.returncode}"
        return result.stdout.strip()
    except Exception as e:
        return f"Something went wrong...{e}"

@st.cache_data(ttl=3600)
def calculate(question):
    question = question.lower().strip()

    question = question.replace("sin(", "sin_rad(")
    question = question.replace("cos(", "cos_rad(")
    question = question.replace("tan(", "tan_rad(")
    try:

        def sin_rad(x):
            return sp.sin(sp.pi / 180 * x)

        def cos_rad(x):
            return sp.cos(sp.pi / 180 * x)

        def tan_rad(x):
            return sp.tan(sp.pi / 180 * x)

        locals_dict = {
            "sin_rad": sin_rad,
            "cos_rad": cos_rad,
            "tan_rad": tan_rad,
            "pi": sp.pi,
            "sqrt": sp.sqrt,
        }

        expression = sp.sympify(question, locals=locals_dict)
        decimal = expression.evalf(5)
        fraction = sp.nsimplify(decimal)
        return f"{fraction}  (~ {decimal:.3f})"

    except sp.SympifyError:
        return "The calculation failed."
    except Exception as e:
        return f"Something went wrong... {e}"

@st.cache_data(ttl=30)
def fetch_alpha(symbol, api_key, premium=False):
    url = "https://www.alphavantage.co/query"

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "full" if premium else 'compact' 
    }

    response = requests.get(url, params=params)
    data = response.json()
    if 'Note' in data:
        st.error("Alpha Vantage Rate Limit Hit! Please try again later or upgrade your key.")
        st.stop()
    
    if 'Information' in data:
        st.error(f'Message from Alpha Vantage: {data["Information"]}')
    if 'Error Message' in data or ValueError in data:
        st.error(f'Message from Alpha Vantage: {data}')

    if "Time Series (Daily)" not in data:
        return pd.DataFrame()

    df = pd.DataFrame.from_dict(
        data["Time Series (Daily)"],
        orient="index"
    )

    df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume"
    }, inplace=True)

    df.index = pd.to_datetime(df.index)
    df = df.reset_index().rename(columns={"index": "Date"})
    df = df.sort_values("Date")

    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    return df

def port(tickers, num_port=3000):
    prices = pd.DataFrame()
    for ticker in tickers:
        df = yf.download(ticker, period='2y', auto_adjust=True)
        if not df.empty:
            prices[ticker] = df['Close']
    if prices.empty or len(prices.columns) < 2:
        st.warning('You need at least 2 tickers.')
        return None
    returns = prices.pct_change().dropna()
    mean = returns.mean() * 252
    cov_matrix = returns.cov() * 252

    result = []

    weight = []

    assets = len(tickers)
    risk_free = 0.0369
    gene = np.random.default_rng()
    for _ in range(num_port):
       
        w = gene.random(assets)
        w = w / w.sum()
        weight.append(w)
        portfolio_return = np.dot(w, mean)
        portfolio_risk =  np.sqrt(w.T @ cov_matrix.values @ w)
        sharpe = (portfolio_return - risk_free) / portfolio_risk

        result.append({'returns': portfolio_return, 'risk': portfolio_risk, 'sharpe':sharpe, 'Weight':w})

    result_df = pd.DataFrame(result)
    max_sharpe = result_df['sharpe'].idxmax()
    min_risk = result_df['risk'].idxmin()
    min_vol = result_df.iloc[min_risk]
    max_sharpe_df = result_df.iloc[max_sharpe]
    fig = go.Figure()


    fig.add_trace(go.Scatter(x=result_df['risk'], y=result_df['returns'], mode = 'markers', marker = dict(
        color=result_df['sharpe'],
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title='Sharpe Ratio'),
        size=4,
        opacity=0.6
    ), name='Chart of Portfolios'))

    fig.add_trace(go.Scatter(
    x=[max_sharpe_df['risk']],
    y=[max_sharpe_df['returns']],
    mode='markers',
    marker=dict(color='red', size=15, symbol='star'),
    name=f'Max Sharpe: {max_sharpe_df["sharpe"]}'
))
    fig.update_layout(title = 'Efficient Frontier', xaxis_title = 'Annual Risk', yaxis_title = 'Annual Returns',  xaxis=dict(tickformat='.0%'),
    yaxis=dict(tickformat='.0%'),
    height=600,
    template='plotly_white')
    
    fig.add_trace(go.Scatter(
    x=[min_vol['risk']],
    y=[min_vol['returns']],
    mode='markers',
    marker=dict(color='green', size=15, symbol='star'),
    name='Min Volatility'
))
    return fig, max_sharpe_df, min_vol, tickers

def stocks():

    try:
        
        alpha_key = st.text_input('Type in your API key from Alpha Vantage (free/paid).', type='password')
        grok_key = st.text_input('Type in your API key from Grok (free/paid).', type='password')
        if not alpha_key:
            st.warning("You must enter your own API key.")
            st.info("NOTE: If you are using a free key, you may have to click the 'Stock Analysis' button twice.")
            st.stop()
        if alpha_key:
            
            user = st.text_input("Choose a stock. ").upper()
            user2 = st.date_input("Choose a starting date. Format as YYYY-MM-DD: ")
            user3 = st.date_input("Choose a ending date. Format as YYYY-MM-DD: ")
            if st.button("Run Stock Analysis"):
                if not user:
                    st.error("Provide a ticker symbol.")

                else:

                    df = fetch_alpha(user, alpha_key, premium=False)  
                    if df.empty:
                        st.error("Invalid ticker or API issue.")
                        st.stop()
                    df = rsi(df)
                    df = macd(df)
                    df = bollinger(df)
                    df = wrap(df)
                    current_macd = df['MACD'].iloc[-1]
                    sig_macd = df['Signal_Line'].iloc[-1]
                    crossover = 'Bullish' if current_macd > sig_macd else 'Bearish'
                    current_rsi = df['RSI'].iloc[-1]
                    

                    df = df[(df["Date"] >= pd.to_datetime(user2)) & (df["Date"] <= pd.to_datetime(user3))]
                    
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    if df.empty:
                        st.error("Please provide a stock ticker.")
                        st.stop()



                    def Cagr(df, price_col):
                        start = df[price_col].iloc[0]
                        end = df[price_col].iloc[-1]
                        days = (df["Date"].iloc[-1] - df["Date"].iloc[0]).days
                        if days == 0 or start == 0:
                            return 0
                        return ((end / start) ** (365 / days) - 1) * 100

                    stock_cagr = Cagr(df, "Close")
                    close = "Close"
                    price = df[close].iloc[-1]
                    last_close = df[close].iloc[-2]
                    price_delta = price - last_close
                    percent_delta = (price_delta / last_close) * 100
                    df["SMA_100"] = df[close].rolling(window=100).mean()
                    df["SMA_50"] = df[close].rolling(window=50).mean()
                    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={user}&apikey={alpha_key}'
                    response = requests.get(url)
                    data = response.json()
                    pe_ratio = (data.get('PERatio', 'N/A'))
                    ps_ratio = data.get('PriceToSalesRatioTTM', 'N/A')
                    pb_ratio = data.get('PriceToBookRatio', 'N/A')
                    profit_margin = data.get('ProfitMargin', 'N/A')
                    forward_pe = data.get('ForwardPE', 'N/A')



                    if df["SMA_50"].isna().iloc[-1]:
                        st.write(
                            "That is not enough range for 50 day SMA. Please choose a higher date range."
                        )
                        st.stop()

                    Support = df[close].rolling(window=100).min()
                    Resistance = df[close].rolling(window=100).max()

                    df["Support"] = Support
                    df["Resistance"] = Resistance

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
                    st.metric(f"Annual Volatility ", f'{annual_vol:.2f}')
                    st.metric(f'ATR', f'{atr(df)}')
                    Percent_Distance_to_Support = (
                        (price - Support.iloc[-1]) / Support.iloc[-1]
                    ) * 100
                    
                    st.metric(
                        f"Percent Away From 50 Day Low", f'{Percent_Distance_to_Support}'
                    )
                    
                    st.metric(f"CAGR", f'{stock_cagr:.2f}')
                    st.metric(f"Sharpe Ratio", f"{sharpness(df)}")
                    st.metric(f'RSI', f"{current_rsi}") 
            
                    st.metric(f'MACD', f'{current_macd}')



                    if yesterday_100 <= yesterday_50 and today_100 > today_50:
                        st.write("GOLDEN CROSS ✨📈")
                        st.balloons()
                    elif yesterday_100 >= yesterday_50 and today_100 < today_50:
                        st.write("DEATH CROSS 📉☠️.")
                        st.snow()
                    else:
                        if today_100 > today_50:
                            st.write("Bullish signs.")
                        else:
                            st.write("Bearish signs.")

                    if vol_ratio > 1.5:
                        st.write("People are buying this stock more than usual! 🔥")
                    elif vol_ratio < 0.5:
                        st.write("People are not buying this stock as much. 🧊")
                    elif pd.isna(vol_ratio):
                        st.write('Something went wrong when calculating the volume ratio.')

                    if price > today_100:
                        st.write("Price is above the 100-day SMA.")
                    else:
                        st.write("Price is below the 100-day SMA.")

                    if price > today_50:
                        st.write("Price is above the 50-day SMA.")
                    else:
                        st.write("Price is below 50-day SMA.")
                    current_vwap = df['VWAP'].iloc[-1]
                    if price > current_vwap:
                        st.write('Bullish Interday Bias')
                    else:
                        st.write('Bearish Interday Bias')
                    
                    st.metric(
                        label="Current Price",
                        value=f"{price:.2f}",
                        delta=f"{percent_delta:.2f}"
                    )
                    st.metric('P/E Ratio',pe_ratio)
                    st.metric('Forward P/E Ratio', forward_pe)
                    st.metric('P/S Ratio', ps_ratio)
                    st.metric('P/B Ratio', pb_ratio)
                    st.metric('Profit Margin', profit_margin)
                    try:
                        peg = float(pe_ratio) / float(Cagr)
                        peg_dis = peg
                        st.metric('PEG Ratio', peg_dis)
                    except Exception:
                        st.error('Error Calculating PEG Ratio.')
                        peg_dis = 'N/A'
                    st.write(f'The MACD crossover is {crossover}.')
                    if crossover == 'Bearish':
                        st.snow()
                    else:
                        st.balloons()
                    st.subheader('News and Sentiment Score')
                    news = sent(user, alpha_key)
                    try:
                        mean_sentiment = sum(item['score'] for item in news) / len(news)
                    except Exception:
                        mean_sentiment = 0
                        st.write('Mean Sentiment: 0')
                    if news:
                        if mean_sentiment != 0:
                            st.write(f'Mean Sentiment Score on a scale of -1 to 1: {mean_sentiment}')
                        else:
                            st.write('Mean Sentiment Score on a scale of -1 to 1: 0')
                            
                    else:
                        st.write('No news was found for this ticker.')
                
                    
                    st.subheader('What the AI says [Beta]')
                    st.info(grok(
                            f"""
                            You are a Senior Equity Research Analyst. Your task is to provide a high-density, 4-sentence synthesis of market data for institutional clients.
                            Round all numbers to the nearest tenth. 
                            Eliminate Filler: "Ban phrases like 'as evidenced by,', 'blind spot' 'the company's,' and 'representing a.' Use direct, punchy descriptors (e.g., 'Indefensible valuation' instead of 'The valuation appears stretched')."
                            Explicitly flag any 'Bullish/Bearish Divergence' when technicals are strong but growth is negative.
                            Bold the category at the start of each sentence (e.g., Posture:, Conviction:, Valuation:).
Use Financial Shorthand: "Instruct the AI to use terms like 'multiple expansion/contraction,' 'technical regime,' 'risk-reward skew,' and 'fundamental decay.'"

The "So What?" Rule: "Every sentence must lead with the conclusion, followed by the supporting data (e.g., 'Avoid: 36.8% volatility' rather than 'We recommend avoiding because volatility is 36.8%')."

TECHNICAL INDICATORS:
- RSI: {current_rsi} (Oversold <30 | Neutral 30-70 | Overbought >70)
- MACD Crossover: {crossover} (Bullish if MACD crosses above signal line, Bearish if below)
- Annual Volatility: {annual_vol} (Low <20% | Moderate 20-40% | High >40%)
- Volume Ratio: {vol_ratio} (vs 20-day avg; >1.5 = elevated interest, <0.5 = weak conviction)

FUNDAMENTAL INDICATORS:
- P/E Ratio: {pe_ratio} (Industry avg ~20-25; higher = growth premium or overvaluation)
- P/B Ratio: {pb_ratio} (>3 may indicate overvaluation; <1 may indicate undervaluation)
- P/S Ratio: {ps_ratio} (High P/S only justified by strong revenue growth)
- CAGR: {stock_cagr} (Compound Annual Growth Rate; benchmark against S&P 500 ~10%)
- PEG Ratio: {peg_dis} (A low PEG ratio means you are paying a bargain price for a company's future growth, where a value under 1.0 suggests the stock is undervalued compared to its earnings potential.)

SENTIMENT:
- Sentiment Score: {mean_sentiment} (Scale: -1 fully negative to +1 fully positive; weight this LESS than quantitative data)


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
                            """
                        , grok_key))
                    
                    plot_df = df.dropna(subset=['MACD', 'Signal_Line', 'MACD_Histogram'])
                    if not plot_df.empty:
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=(f'{user} Stock Analysis', 'MACD'), row_width=[0.3, 0.7])
                        
                        price_path ,p5, p50, p95 = sim(df)
                        days = list(range(30))
                        fig_sim = go.Figure()


                        
                        fig_sim.add_trace(go.Scatter(
                            x=days, y=p5,
                            fill='tonexty',
                            fillcolor='rgba(100, 149, 237, 0.3)',
                            line=dict(color='rgba(0,0,0,0)'),
                            name='5th–95th Percentile'
                        ))

        
                        fig_sim.add_trace(go.Scatter(
                            x=days, y=p50,
                            line=dict(color='royalblue', width=2),
                            name='Median Path'
                        ))
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Closing Price', line=dict(color='gold', width=1)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_50'], name='50 Day SMA', line=dict(color='orange', width=1)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_100'], name='100 Day SMA', line=dict(color='orange', width=1)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_Up'], line=dict(color='rgba(0,0,0,0)'), showlegend=False), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_Down'], line=dict(color='rgba(0,0,0,0)'), fill='tonexty', fillcolor='rgba(173, 216, 230, 0.2)', name='Bollinger Band'), row=1, col=1)                    
                        fig.add_trace(go.Bar(x=df['Date'], y=df['MACD_Histogram'], name='Histogram'), row=2, col=1)
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD', line=dict(color='black')), row=2, col=1)
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['Signal_Line'], name='Signal', line=dict(color='red')), row=2, col=1)
                        fig.add_trace(go.Scatter(x=df['Date'], y=df['VWAP'], name='VWAP', line=dict(color='red')), row=1, col=1)
                        fig.update_layout(
                                xaxis_rangeslider_visible=False,
                                height=800,
                                template="plotly_white",
                                showlegend=True
                            )

                        st.plotly_chart(fig, use_container_width=True)
                        st.plotly_chart(fig_sim, use_container_width=True)
                        
                        pdf_buffer = io.BytesIO()

                        st.write('The app is for educational/informational purposes, not financial advice.')
                        st.write('Talos AI is an experimental tool. Trading small-caps involves high risk of capital loss.')
                        with PdfPages(pdf_buffer) as pdf:
                            fig.write_image("chart.png")
                            

                           
                            fig.update_xaxes(title_text='Date', tickangle = -45)
                            fig.update_yaxes(title_text='Price', tickangle = -45)
                        pdf_buffer.seek(0)
                        st.download_button(
                            label='Download Report as PDF',
                            data=pdf_buffer,
                            file_name=f'{user}_analysis.pdf',
                            mime='application/pdf')
                


    except FileNotFoundError:
        return "The file was not found..."

    except PermissionError:
        return "You do not have permissions for this file."



def calendar():

    if "reminders" not in st.session_state:
        st.session_state.reminders = []
    date = st.date_input("Input a date.")
    reminder = st.text_input("What are you setting a reminder for?")

    if st.button("Save Reminder"):
        if reminder:
            st.session_state.reminders.append({"date": date, "reminder": reminder})
            st.write(f"Saved {reminder} on {date}")
        else:
            st.warning("Provide a reminder.")

    st.subheader("Your Reminders")
    for item in st.session_state.reminders:
        st.write(f"🔔 {item['reminder']} on {item['date']}")





@st.fragment(run_every=1)
def system_stats():
    st.subheader("Hardware Monitor")

    col1, col2, col3 = st.columns(3)
    cpu_placeholder = col1.empty()
    ram_placeholder = col2.empty()
    freq_placeholder = col3.empty()

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    freq = psutil.cpu_freq().current

    with cpu_placeholder.container(border=True):
        st.plotly_chart(gauge(cpu, 'CPU', 'green' if cpu < 70 else 'red'), use_container_width=True)

    with ram_placeholder.container(border=True):
        st.plotly_chart(gauge(ram, 'RAM', 'blue'), use_container_width=True)

    with freq_placeholder.container(border=True):
        st.plotly_chart(gauge(freq, 'CPU Frequency', 'yellow'), use_container_width=True)

    time.sleep(0.5)




def create_sql():
    conn = sqlite3.connect('talos.db', check_same_thread=False)
    return conn
def initialize_db():
    conn = create_sql()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            password_hash TEXT
        )
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users(username)
        )''')
    conn.commit()
    conn.close()
def pull_data():
    conn = sqlite3.connect('talos.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT username, name, email, password_hash FROM users')
    rows = cursor.fetchall()
    conn.commit()
    conn.close()
    creds = {'usernames':{}}
    for row in rows:
        username, name, email, password_hash = row
        creds['usernames'][username] = {'name':name, 'password':password_hash, 'email':email, 'logged_in':False}
    
    return creds
def save_chat(username, role, content):
    conn = create_sql()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (username, role, content) VALUES (?, ?, ?)', (username, role, content) )
    conn.commit()
    conn.close()
    

def load_chat(username):
    conn = create_sql()
    cursor = conn.cursor()
    cursor.execute('SELECT role, content FROM chat_history WHERE username = ? ORDER BY timestamp ASC', (username, ))
    rows = cursor.fetchall()
    conn.close()
    hist = []
    for row in rows:
        hist.append({'role': row[0], 'content':row[1]})
    return hist    


def stock_analysis(uploaded):

    st.write('Stock Analysis')

    if uploaded:
        try:
            if uploaded.name.endswith('.json'):
                df = pd.read_json(uploaded)
            elif uploaded.name.endswith('.csv'):
                df = pd.read_csv(uploaded)

            if 'Date' not in df.columns or 'Close' not in df.columns:
                st.error('You must have Date/Close columns.')
                return
            
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')


            st.dataframe(df.tail())

            start = df['Close'].iloc[-2]
            end = df['Close'].iloc[-1]
            stock_return = ((end - start)/start) * 100

            st.metric('Starting Price',f'${start:.2f}')
            st.metric('Ending Price',f'${end:.2f}')
            st.metric('Total Returns in percent', f'{stock_return:.2f}')



        except Exception as e:
            st.error('Something went wrong...')
            return f'Something went wrong...{e}'
            
def clear_chat(username):
    conn = create_sql()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE username = ?', (username,))
    conn.commit()
    conn.close()
def stats():
    conn = create_sql()
    cursor = conn.cursor()
    
    query = '''
        SELECT u.username, u.name, COUNT(c.id) as message_count
        FROM users u
        LEFT JOIN chat_history c ON u.username = c.username
        GROUP BY u.username
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows