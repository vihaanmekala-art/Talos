# Efficient Frontier Portfolio Optimizer

## Overview
This project is a Streamlit-based financial analysis application that analyzes stocks
and applies **mean–variance optimization** (Efficient Frontier theory, Nobel Prize in Economics 1990)
to determine optimal capital allocation between assets based on risk and return.

The tool is designed for **educational and analytical purposes**, helping users
understand portfolio construction, diversification, and risk–return tradeoffs.

---

## Motivation
I built this project to explore how classical financial theory can be implemented
programmatically and applied to real market data. Many investing tools provide
allocations without transparency; this app emphasizes **explainability** and
user understanding.

---

## Methodology
The application implements **Modern Portfolio Theory**, including:

- Expected return estimation using historical price data
- Covariance matrix computation to model asset correlations
- Mean–variance optimization to construct the efficient frontier
- Identification of minimum-variance and optimal-risk portfolios
- Capital allocation based on user-defined investment amount

Optimization is performed under standard constraints (fully invested, long-only),
with visualizations to help interpret results.

---

## Features
- Interactive stock analysis dashboard
- Efficient frontier visualization
- Optimal portfolio weight calculation
- Capital allocation calculator
- Risk and return metrics for each portfolio

---

## Example Output
*(Add screenshots or a GIF of the Streamlit app here)*

---

## Assumptions & Limitations
- Returns are estimated from historical data and are not predictive
- Mean–variance optimization assumes stable correlations and normally distributed returns
- Transaction costs, taxes, and liquidity constraints are not modeled
- This project is **not financial advice** and is intended for educational use only

---

## Tech Stack
- Python
- Streamlit
- NumPy
- Pandas
- SciPy
- Financial data APIs (e.g., yfinance)

---

## Adoption
In the past 14 days, this project has been cloned by **50+ unique users**, indicating
real-world interest for educational and analytical use.

---

## How to Run Locally
```bash
git clone https://github.com/vihaanmekala-art/Talos.git
cd Talos
pip install -r requirements.txt
streamlit run streamlit_app.py

## 🚀 Try Talos
Try Talos here: [https://talos-production.up.railway.app/] 
