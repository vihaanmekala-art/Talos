from flask import Flask, jsonify, request
from flask_cors import CORS
import streamlit_util as util
import numpy as np
import math as math

app = Flask(__name__)

CORS(app)

@app.route('/api/stock', methods=['GET'])


def clean(val):
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def get_stock():
    symbol = request.args.get('symbol')
    api_key = request.args.get('api_key')
    df = util.fetch_alpha(symbol, api_key)
    df = util.rsi(df)
    df = util.macd(df)
    df = util.bollinger(df)
    df = util.wrap(df)
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_100'] = df['Close'].rolling(window=100).mean()
    last = df.iloc[-1]
    print(df.columns.tolist())
    prices_df = df[['Date', 'Close', 'SMA_50', 'VWAP']].copy()
    prices_df = prices_df.fillna(0)
    return jsonify({
        'prices': prices_df.to_dict(orient='records'),
        'metrics': {
            'rsi': clean(last['RSI']),
            'macd': clean(last['MACD']),
            'signal': clean(last['Signal_Line']),
            'vwap': clean(last['VWAP']),
            'sharpe': clean(util.sharpness(df)),
            'atr': clean(float(util.atr(df))),
            'close': clean(last['Close']),
            'volume': int(last['Volume']),
        }
    })

if __name__ == '__main__':
    app.run(debug=True, use_reloader = False)