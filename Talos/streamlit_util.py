"""
Legacy compatibility shim for streamlit_util.

All functions have been moved to dedicated modules:
- portfolio.py   -> port()
- analysis.py    -> stocks(), stock_analysis()
- valuation.py   -> intr()
- macro.py       -> get_macro(), get_risk_free(), show_macro()
- ai.py          -> calculate(), groq()
- technical.py   -> rsi(), macd(), bollinger(), atr(), sim(), sharpness(), wrap()
"""

raise ImportError(
    "streamlit_util is deprecated. Import from the specific modules instead: "
    "portfolio, analysis, valuation, macro, ai, technical."
)
