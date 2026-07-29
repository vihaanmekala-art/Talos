

from __future__ import annotations

import numpy as np
import pandas as pd


def wrap(df: pd.DataFrame) -> pd.DataFrame | None:
    df = df.copy()
    try:
        df["Ty"] = (df["High"] + df["Low"] + df["Close"]) / 3
    except ZeroDivisionError:
        return None

    df["Cum_TP_Vol"] = (df["Ty"] * df["Volume"]).cumsum()
    df["Cum_Vol"] = df["Volume"].cumsum()
    df["VWAP"] = df["Cum_TP_Vol"] / df["Cum_Vol"]
    return df


def atr(df: pd.DataFrame, period: int = 14) -> float:
    df = df.copy()
    high_low = df["High"] - df["Low"]
    high_prev_close = (df["High"] - df["Close"].shift(1)).abs()
    low_prev_close = (df["Low"] - df["Close"].shift(1)).abs()

    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1)
    tr = tr.max(axis=1)
    atr_val = tr.rolling(window=period).mean()
    return atr_val.iloc[-1]


def bollinger(df: pd.DataFrame, window: int = 20, num_std: int = 2) -> pd.DataFrame:
    df = df.copy()
    df["SMA_20"] = df["Close"].rolling(window=window).mean()
    df["BB_Up"] = df["SMA_20"] + num_std * df["Close"].rolling(window=window).std()
    df["BB_Down"] = df["SMA_20"] - num_std * df["Close"].rolling(window=window).std()
    return df


def macd(df: pd.DataFrame) -> pd.DataFrame:
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Histogram"] = df["MACD"] - df["Signal_Line"]
    return df


def rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    df = df.dropna()
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def sharpness(df: pd.DataFrame, risk_free: float) -> float:
    returns = df["Close"].dropna().pct_change().dropna()
    daily_rf = (1 + risk_free) ** (1 / 252) - 1
    mean = returns.mean()
    vola = returns.std()
    if vola == 0:
        return np.nan
    sharpe_ratio = ((mean - daily_rf) / vola) * np.sqrt(252)
    return sharpe_ratio


def sim(df: pd.DataFrame):
    returns = df["Close"].dropna().pct_change()
    price = df["Close"].iloc[-1]

    vola = returns.std()
    ret = returns.mean()

    rng = np.random.default_rng()
    noise = rng.normal(ret, vola, (30, 1000))
    price_path = price * (1 + noise).cumprod(axis=0)

    p5 = np.percentile(price_path, 5, axis=1)
    p50 = np.percentile(price_path, 50, axis=1)
    p95 = np.percentile(price_path, 95, axis=1)

    return price_path, p5, p50, p95
