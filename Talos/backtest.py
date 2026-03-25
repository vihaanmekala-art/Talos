import numpy as np
import pandas as pd

def backtester(df, buy_rsi = 30, sell_rsi=70, starter_cash = 10000):
    rsi = df['RSI'].values
    close = df['Close'].values
    signals = np.where(rsi < buy_rsi, 1, np.where(rsi > sell_rsi, -1, 0))
    position = np.clip(np.cumsum(signals), 0, 1)
    returns = np.diff(close) / close[:-1]
    position = position[:-1]

    strat_return = position * returns

    portfolio = starter_cash * np.cumprod(1 + strat_return)

    tot_returns = (portfolio[-1] - starter_cash) * 100 / starter_cash

    sharpe = np.mean(strat_return) / np.std(strat_return) * np.sqrt(252)
   
    buy = len(np.where(signals == 1)[0])
    sell = len(np.where(signals == -1)[0])
    portfolio = pd.Series(portfolio)
    return {
        "portfolio": portfolio,
        "total_return": tot_returns,
        "sharpe": sharpe,
        "buy": buy,
        'sell':sell
    }